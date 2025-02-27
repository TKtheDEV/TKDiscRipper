import psutil
import platform
import subprocess
import GPUtil
from typing import Dict

def get_system_info() -> Dict:
    """Retrieve system information such as OS, CPU, Memory, Storage, and GPU details."""
    
    # OS Information
    os_info = {
        "os": platform.system(),
        "os_version": platform.version(),
        "os_release": platform.release(),
        "uptime": psutil.boot_time()
    }
    
    # CPU Information
    cpu_info = {
        "model": platform.processor(),
        "cores": psutil.cpu_count(logical=False),
        "threads": psutil.cpu_count(logical=True),
        "frequency": psutil.cpu_freq().max,
        "usage": psutil.cpu_percent(interval=1)
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