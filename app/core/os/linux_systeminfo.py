import platform
import psutil
import subprocess
import time
import socket
import json
from typing import Dict

class LinuxSystemInfo:
    def get_system_info(self) -> Dict:
        return {
            "os_info": self._get_os_info(),
            "cpu_info": self._get_cpu_info(),
            "memory_info": self._get_memory(),
            "storage_info": self._get_storage(),
            "gpu_info": self._get_gpu(),
            "hwenc_info": self._get_hwenc()
        }

    def _get_os_info(self) -> Dict:
        try:
            with open("/etc/os-release", "r") as f:
                os_release = f.readlines()
                os_version = next((line.split("=")[1].strip().strip('"') for line in os_release if line.startswith("VERSION=")), platform.version())
        except FileNotFoundError:
            os_version = platform.version()

        return {
            "os": platform.system(),
            "os_version": os_version,
            "kernel": platform.release(),
            "uptime": self._format_uptime(psutil.boot_time())
        }

    def _format_uptime(self, boot_time: float) -> str:
        seconds = int(time.time() - boot_time)
        days, seconds = divmod(seconds, 86400)
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        return f"{days}d {hours}h {minutes}m {seconds}s"

    def _get_cpu_info(self) -> Dict:
        try:
            with open("/proc/cpuinfo", "r") as f:
                model = next((line.split(": ")[1].strip() for line in f if line.startswith("model name")), platform.processor())
        except FileNotFoundError:
            model = platform.processor()

        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp = int(f.read().strip()) / 1000.0
        except:
            temp = "N/A"

        return {
            "model": model,
            "cores": psutil.cpu_count(logical=False),
            "threads": psutil.cpu_count(logical=True),
            "frequency": int(psutil.cpu_freq().current),
            "usage": psutil.cpu_percent(interval=1),
            "temperature": temp
        }

    def _get_memory(self):
        mem = psutil.virtual_memory()
        return {
            "total": mem.total,
            "available": mem.available,
            "used": mem.used,
            "percent": mem.percent
        }

    def _get_storage(self):
        disk = psutil.disk_usage('/')
        return {
            "total": disk.total,
            "used": disk.used,
            "available": disk.free,
            "percent": disk.percent
        }

    def _get_gpu(self) -> Dict:
        """Retrieve GPU information using LACT."""
        gpu_info = []
        device_list = self._query_lact({"command": "list_devices"})
        
        if device_list.get("status") == "ok":
            for device in device_list.get("data", []):
                device_id = device.get("id")
                stats = self._query_lact({"command": "device_stats", "args": {"id": device_id}})
                
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
                        "usuage": round(data.get("busy_percent", 0.0), 1),
                        "temperature": temperature,
                        "power_draw": round(data.get("power", {}).get("current", 0.0), 1)
                    })
        
        return gpu_info if gpu_info else "No GPU detected or LACT not running"

    def _query_lact(self, command: Dict) -> Dict:
        """Send command to lactd Unix socket and return response."""
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                client.connect("/run/lactd.sock")
                client.sendall(json.dumps(command).encode() + b"\n")
                response = client.recv(4096)
                return json.loads(response.decode())
        except (FileNotFoundError, ConnectionRefusedError, json.JSONDecodeError):
            return {}

    def _get_hwenc(self):
        try:
            result = subprocess.run(
                ["flatpak", "run", "--command=HandBrakeCLI", "fr.handbrake.ghb", "-h"],
                capture_output=True, text=True, check=True
            )
            output = result.stdout.splitlines()

            all_encoders = [line.strip() for line in output if any(v in line for v in ["nvenc_", "qsv_", "vce_"])]
            
            def extract_codecs(enc_list, prefix):
                return sorted({e.replace(prefix, "") for e in enc_list if e.startswith(prefix)})

            encoders = {
                "nvenc": extract_codecs(all_encoders, "nvenc_"),
                "qsv": extract_codecs(all_encoders, "qsv_"),
                "vce": extract_codecs(all_encoders, "vce_")
            }

            return {
                "vendors": {
                    "nvenc": {
                        "label": "NVIDIA NVENC",
                        "available": bool(encoders["nvenc"]),
                        "codecs": encoders["nvenc"]
                    },
                    "qsv": {
                        "label": "Intel QSV",
                        "available": bool(encoders["qsv"]),
                        "codecs": encoders["qsv"]
                    },
                    "vce": {
                        "label": "AMD VCE",
                        "available": bool(encoders["vce"]),
                        "codecs": encoders["vce"]
                    }
                }
            }

        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"[get_hwenc] HandBrake CLI failed: {e}")
            return {
                "vendors": {
                    "nvenc": {"label": "NVIDIA NVENC", "available": False, "codecs": []},
                    "qsv": {"label": "Intel QSV", "available": False, "codecs": []},
                    "vce": {"label": "AMD VCE", "available": False, "codecs": []}
                }
            }




if __name__ == "__main__":
    print(LinuxSystemInfo().get_system_info())