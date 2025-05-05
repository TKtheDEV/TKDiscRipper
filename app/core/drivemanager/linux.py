import subprocess
from app.core.drive_tracker import drive_tracker

def scan_drives():
    try:
        output = subprocess.check_output(["lsblk", "-o", "NAME,TYPE,MODEL", "-dn"], text=True)
        for line in output.strip().splitlines():
            parts = line.strip().split(None, 2)
            if len(parts) < 3:
                continue
            name, dtype, model = parts
            if dtype != "rom":
                continue
            path = f"/dev/{name}"
            capability = detect_capability(path)
            label = detect_label(path)
            drive_tracker.add_or_update_drive(path, model, capability, disc_label=label)
    except Exception as e:
        pass

def detect_capability(device: str) -> str:
    try:
        out = subprocess.check_output(["udevadm", "info", "--query=property", "--name", device], text=True)
        if "ID_CDROM_BD=1" in out:
            return "BLURAY"
        elif "ID_CDROM_DVD=1" in out:
            return "DVD"
        elif "ID_CDROM=1" in out:
            return "CD"
    except:
        pass
    return "UNKNOWN"

def detect_label(device: str) -> str:
    try:
        result = subprocess.check_output(["lsblk", "-no", "LABEL", device], text=True)
        label = result.strip()
        return label if label else None
    except:
        return None

def eject_drive(device: str) -> bool:
    try:
        subprocess.run(["eject", device], check=True)
        return True
    except subprocess.CalledProcessError:
        return False
