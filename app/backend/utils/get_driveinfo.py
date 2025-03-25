import os
import subprocess
from typing import List, Dict
import json

def get_drive_info() -> List[Dict]:
    """Retrieve a list of optical drives with model, capability, status, and disc label."""
    drives = []

    try:
        result = subprocess.run(["lsblk", "-J"], capture_output=True, text=True, check=True)
        lsblk_output = result.stdout
    except subprocess.CalledProcessError:
        return [{"error": "Failed to retrieve drive information"}]

    lsblk_data = json.loads(lsblk_output)

    for device in lsblk_data.get("blockdevices", []):
        if "rom" in device.get("type", ""):
            name = device.get("name", "")
            path = os.path.realpath(f"/dev/{name}")
            model = get_drive_model(path)
            label = get_disc_label(path)
            drive = {
                "model": model,
                "path": path,
                "capability": get_drive_capability(name),
                "status": get_drive_status(name),
                "disc_label": label  # ✅ added
            }
            drives.append(drive)

    return drives

def get_drive_model(device_path: str) -> str:
    try:
        result = subprocess.run(["lsblk", "-no", "ID", device_path], capture_output=True, text=True, check=True)
        raw_id = result.stdout.strip()
        return raw_id.rsplit("_", 1)[0] if "_" in raw_id else raw_id
    except subprocess.CalledProcessError:
        return "Unknown"

def get_disc_label(device_path: str) -> str:
    try:
        result = subprocess.run(["lsblk", "-no", "LABEL", device_path], capture_output=True, text=True)
        return result.stdout.strip() or "UNTITLED"
    except subprocess.CalledProcessError:
        return "UNTITLED"

def get_drive_capability(device_name: str) -> str:
    try:
        result = subprocess.run(
            ["udevadm", "info", "--query=property", f"--name=/dev/{device_name}"],
            capture_output=True, text=True, check=True
        )
        props = result.stdout.split("\n")
        if any("ID_CDROM_BD=1" in p for p in props):
            return "BD"
        if any("ID_CDROM_DVD=1" in p for p in props):
            return "DVD"
        if any("ID_CDROM=1" in p for p in props):
            return "CD"
        return "Unknown"
    except subprocess.CalledProcessError:
        return "Unknown"

def get_drive_status(device_name: str) -> str:
    try:
        result = subprocess.run(["fuser", f"/dev/{device_name}"], capture_output=True, text=True)
        return "ripping" if result.stdout.strip() else "idle"
    except subprocess.CalledProcessError:
        return "unknown"

if __name__ == "__main__":
    import json
    print(json.dumps(get_drive_info(), indent=4))