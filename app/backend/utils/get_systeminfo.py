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
        with open("/sys/class/thermal/cooling_device0/temp", "r") as f:
            cpu_temp = int(f.read().strip()) / 1000.0
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
            "temperature": gpu.temperature
        } for gpu in gpus]
    except Exception:
        gpu_info = "No GPU detected or GPUtil not installed"

    return {
        "os_info": os_info,
        "cpu_info": cpu_info,
        "memory_info": memory_info,
        "storage_info": storage_info,
        "gpu_info": gpu_info
    }


if __name__ == "__main__":
    import json
    print(json.dumps(get_system_info(), indent=4))