import os
import subprocess
from typing import List, Dict

def get_drive_info() -> List[Dict]:
    """Retrieve a list of available optical drives and their status."""
    drives = []
    
    try:
        result = subprocess.run(["lsblk", "-J"], capture_output=True, text=True, check=True)
        lsblk_output = result.stdout
    except subprocess.CalledProcessError:
        return [{"error": "Failed to retrieve drive information"}]
    
    import json
    lsblk_data = json.loads(lsblk_output)
    
    for device in lsblk_data.get("blockdevices", []):
        if "rom" in device.get("type", ""):  # Detect optical drives
            drive = {
                "model": device.get("model", "Unknown"),
                "path": f"/dev/{device.get('name', 'Unknown')}",
                "capabilities": get_drive_capabilities(device.get("name", "")),
                "status": get_drive_status(device.get("name", ""))
            }
            drives.append(drive)
    
    return drives

def get_drive_capabilities(device_name: str) -> List[str]:
    """Detects drive capabilities (CD/DVD/BD)."""
    capabilities = []
    
    try:
        result = subprocess.run(["udevadm", "info", f"--query=property", f"--name=/dev/{device_name}"], capture_output=True, text=True, check=True)
        properties = result.stdout.split("\n")
        
        if any("ID_CDROM=1" in prop for prop in properties):
            capabilities.append("CD")
        if any("ID_CDROM_DVD=1" in prop for prop in properties):
            capabilities.append("DVD")
        if any("ID_CDROM_BD=1" in prop for prop in properties):
            capabilities.append("BD")
    except subprocess.CalledProcessError:
        capabilities.append("Unknown")
    
    return capabilities

def get_drive_status(device_name: str) -> str:
    """Checks if a drive is idle or in use."""
    try:
        result = subprocess.run(["fuser", f"/dev/{device_name}"], capture_output=True, text=True)
        return "ripping" if result.stdout.strip() else "idle"
    except subprocess.CalledProcessError:
        return "unknown"

if __name__ == "__main__":
    import json
    print(json.dumps(get_drive_info(), indent=4))