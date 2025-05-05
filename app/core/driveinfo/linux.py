import os
import subprocess
import json
from typing import List, Dict

class LinuxDriveInfo:
    def get_drive_info(self) -> List[Dict]:
        drives = []
        try:
            result = subprocess.run(["lsblk", "-J"], capture_output=True, text=True, check=True)
            lsblk_data = json.loads(result.stdout)
        except subprocess.CalledProcessError:
            return [{"error": "Failed to retrieve drive information"}]

        for device in lsblk_data.get("blockdevices", []):
            if "rom" in device.get("type", ""):
                name = device.get("name", "")
                path = os.path.realpath(f"/dev/{name}")
                drives.append({
                    "model": self._get_drive_model(path),
                    "path": path,
                    "capability": self._get_drive_capability(name),
                    "status": self._get_drive_status(name),
                    "disc_label": self._get_disc_label(path)
                })
        return drives

    def _get_drive_model(self, device_path: str) -> str:
        try:
            result = subprocess.run(["lsblk", "-no", "ID", device_path], capture_output=True, text=True, check=True)
            raw_id = result.stdout.strip()
            return raw_id.rsplit("_", 1)[0] if "_" in raw_id else raw_id
        except subprocess.CalledProcessError:
            return "Unknown"

    def _get_disc_label(self, device_path: str) -> str:
        try:
            result = subprocess.run(["lsblk", "-no", "LABEL", device_path], capture_output=True, text=True)
            return result.stdout.strip() or "UNTITLED"
        except subprocess.CalledProcessError:
            return "UNTITLED"

    def _get_drive_capability(self, device_name: str) -> str:
        try:
            result = subprocess.run(
                ["udevadm", "info", "--query=property", f"--name=/dev/{device_name}"],
                capture_output=True, text=True, check=True
            )
            props = result.stdout.splitlines()
            if any("ID_CDROM_BD=1" in p for p in props): return "BD"
            if any("ID_CDROM_DVD=1" in p for p in props): return "DVD"
            if any("ID_CDROM=1" in p for p in props): return "CD"
            return "Unknown"
        except subprocess.CalledProcessError:
            return "Unknown"

    def _get_drive_status(self, device_name: str) -> str:
        try:
            result = subprocess.run(["fuser", f"/dev/{device_name}"], capture_output=True, text=True)
            return "ripping" if result.stdout.strip() else "idle"
        except subprocess.CalledProcessError:
            return "unknown"
