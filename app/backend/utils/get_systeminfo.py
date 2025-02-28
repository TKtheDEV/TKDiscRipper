import psutil
import platform
import subprocess
import GPUtil
from typing import Dict
import time


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
        return "couldnt read"
    return platform.processor()

#Check if NVENC, QSV, or VCE hardware encoders are available in HandBrake
def get_hwenc_info() -> Dict:
    try:
        result = subprocess.run(["HandBrakeCLI", "-h"], capture_output=True, text=True, check=True)
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

def get_system_info() -> Dict:
    """Retrieve system information such as OS, CPU, Memory, Storage, and GPU details."""

    # OS Information
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
            cpu_temp = str(int(f.read().strip()) / 1000.0)
    except (FileNotFoundError, ValueError):
        cpu_temp = "Not available"

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
        "total": int(mem.total / 1048576),
        "available": int(mem.available / 1048576),
        "used": int(mem.used / 1048576),
        "percent": mem.percent
    }

    # Storage Information
    disk = psutil.disk_usage('/')
    storage_info = {
        "total": int(disk.total / 1048576),
        "used": int(disk.used / 1048576),
        "free": int(disk.free / 1048576),
        "percent": disk.percent
    }

    # GPU Information (Using GPUtil)
    try:
        gpus = GPUtil.getGPUs()
        gpu_info = [{
            "model": gpu.name,
            "total_memory": gpu.memoryTotal,
            "used_memory": gpu.memoryUsed,
            "free_memory": gpu.memoryTotal - gpu.memoryUsed,
            "percent_memory": round((gpu.memoryUsed / gpu.memoryTotal) * 100 if gpu.memoryTotal > 0 else 0, 1),
            "utilization": gpu.load * 100,
            "temperature": str(gpu.temperature)
        } for gpu in gpus]
    except Exception:
        gpu_info = "No GPU detected or GPUtil not installed"

    return {
        "os_info": os_info,
        "cpu_info": cpu_info,
        "memory_info": memory_info,
        "storage_info": storage_info,
        "gpu_info": gpu_info,
        "hwenc_info": get_hwenc_info()
    }



if __name__ == "__main__":
    import json
    print(json.dumps(get_system_info(), indent=4))