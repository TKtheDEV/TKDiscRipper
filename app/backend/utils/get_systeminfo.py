import psutil
import platform
import subprocess
import json
import time
import socket
from typing import Dict

def format_uptime(uptime: float) -> str:
    seconds = int(time.time() - uptime)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return f"{days}d {hours}h {minutes}m {seconds}s"

def get_cpu_model() -> str:
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f.readlines():
                if line.startswith("model name"):
                    return line.split(": ")[1].strip()
    except FileNotFoundError:
        return platform.processor()
    return platform.processor()

def get_hwenc_info() -> Dict:
    try:
        result = subprocess.run(["flatpak", "run", "--command=HandBrakeCLI", "fr.handbrake.ghb", "-h"], capture_output=True, text=True, check=True)
        output = result.stdout.splitlines()
        encoders = {
            "nvenc": [line.strip() for line in output if "nvenc_" in line],
            "qsv": [line.strip() for line in output if "qsv_" in line],
            "vce": [line.strip() for line in output if "vce_" in line],
        }
        return {
            "nvenc": bool(encoders["nvenc"]),
            "qsv": bool(encoders["qsv"]),
            "vce": bool(encoders["vce"]),
            "encoders": encoders
        }
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {
            "nvenc": False,
            "qsv": False,
            "vce": False,
            "encoders": {
                "nvenc": [],
                "qsv": [],
                "vce": []
            }
        }

def query_lact(command: Dict) -> Dict:
    """Send command to lactd Unix socket and return response."""
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect("/run/lactd.sock")
            client.sendall(json.dumps(command).encode() + b"\n")
            response = client.recv(4096)
            return json.loads(response.decode())
    except (FileNotFoundError, ConnectionRefusedError, json.JSONDecodeError):
        return {}

def get_gpu_info() -> Dict:
    """Retrieve GPU information using LACT."""
    gpu_info = []
    device_list = query_lact({"command": "list_devices"})
    
    if device_list.get("status") == "ok":
        for device in device_list.get("data", []):
            device_id = device.get("id")
            stats = query_lact({"command": "device_stats", "args": {"id": device_id}})
            
            if stats.get("status") == "ok":
                data = stats.get("data", {})
                temps = data.get("temps", {})
                temperature = temps.get("edge", {}).get("current") or temps.get("GPU", {}).get("current", 0.0)
                
                gpu_info.append({
                    "model": device.get("name", "Unknown"),
                    "total_memory": data.get("vram", {}).get("total", 0),
                    "used_memory": data.get("vram", {}).get("used", 0),
                    "free_memory": data.get("vram", {}).get("total", 0) - data.get("vram", {}).get("used", 0),
                    "percent_memory": round((data.get("vram", {}).get("used", 0) / data.get("vram", {}).get("total", 1)) * 100, 1),
                    "utilization": round(data.get("busy_percent", 0.0), 1),
                    "temperature": temperature,
                    "power_draw": round(data.get("power", {}).get("current", 0.0), 1)
                })
    
    return gpu_info if gpu_info else "No GPU detected or LACT not running"

def get_system_info() -> Dict:
    """Retrieve system information such as OS, CPU, Memory, Storage, and GPU details."""
    try:
        with open("/etc/os-release", "r") as f:
            os_release = f.readlines()
            os_version = next((line.split("=")[1].strip().strip('"') for line in os_release if line.startswith("VERSION=")), platform.version())
    except FileNotFoundError:
        os_version = platform.version()

    os_info = {
        "os": platform.system(),
        "os_version": os_version,
        "kernel": platform.release(),
        "uptime": format_uptime(psutil.boot_time())
    }

    # CPU Temperature
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            cpu_temp = int(f.read().strip()) / 1000.0
    except (FileNotFoundError, ValueError):
        cpu_temp = "Could not be read"

    # CPU Information
    cpu_info = {
        "model": get_cpu_model(),
        "cores": psutil.cpu_count(logical=False),
        "threads": psutil.cpu_count(logical=True),
        "frequency": int(psutil.cpu_freq().current),
        "usage": psutil.cpu_percent(interval=1),
        "temperature": cpu_temp
    }

    # Memory Information
    mem = psutil.virtual_memory()
    memory_info = {
        "total": mem.total,
        "available": mem.available,
        "used": mem.used,
        "percent": mem.percent
    }

    # Storage Information
    disk = psutil.disk_usage('/')
    storage_info = {
        "total": disk.total,
        "used": disk.used,
        "free": disk.free,
        "percent": disk.percent
    }

    return {
        "os_info": os_info,
        "cpu_info": cpu_info,
        "memory_info": memory_info,
        "storage_info": storage_info,
        "gpu_info": get_gpu_info(),
        "hwenc_info": get_hwenc_info()
    }

if __name__ == "__main__":
    print(json.dumps(get_system_info(), indent=4))
