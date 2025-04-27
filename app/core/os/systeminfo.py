import platform

if platform.system() == "Linux":
    from app.core.os.linux_systeminfo import LinuxSystemInfo as SystemInfo
elif platform.system() == "Windows":
    # Placeholder for future support
    class SystemInfo:
        def get_system_info(self):
            return {
                "os_info": {
                    "os": "Windows",
                    "os_version": "Unknown",
                    "kernel": "Unknown",
                    "uptime": "Unknown"
                },
                "cpu_info": {
                    "model": "Unknown",
                    "cores": 0,
                    "threads": 0,
                    "frequency": 0,
                    "usage": 0,
                    "temperature": "N/A"
                },
                "memory_info": {
                    "total": 0,
                    "available": 0,
                    "used": 0,
                    "percent": 0
                },
                "storage_info": {
                    "total": 0,
                    "used": 0,
                    "available": 0,
                    "percent": 0
                },
                "gpu_info": [],
                "hwenc_info": {}
            }
elif platform.system() == "Darwin":
    # Placeholder for future support
    class SystemInfo:
        def get_system_info(self):
            return {
                "os_info": {
                    "os": "macOS",
                    "os_version": "Unknown",
                    "kernel": "Unknown",
                    "uptime": "Unknown"
                },
                "cpu_info": {
                    "model": "Unknown",
                    "cores": 0,
                    "threads": 0,
                    "frequency": 0,
                    "usage": 0,
                    "temperature": "N/A"
                },
                "memory_info": {
                    "total": 0,
                    "available": 0,
                    "used": 0,
                    "percent": 0
                },
                "storage_info": {
                    "total": 0,
                    "used": 0,
                    "available": 0,
                    "percent": 0
                },
                "gpu_info": [],
                "hwenc_info": {}
            }
else:
    raise RuntimeError(f"Unsupported OS: {platform.system()}")
