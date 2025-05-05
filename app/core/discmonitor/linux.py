import subprocess
import threading
import re
from app.core.drive_tracker import drive_tracker as tracker
from app.core.drivemanager import linux as drivemanager

def monitor_disc_events():
    def _worker():
        try:
            process = subprocess.Popen(
                ["udevadm", "monitor", "--subsystem-match=block", "--property"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )

            current_dev = None
            for line in process.stdout:
                line = line.strip()
                if line.startswith("KERNEL[") or line == "":
                    continue
                if line.startswith("DEVNAME="):
                    current_dev = line.split("=")[1]
                elif line.startswith("ID_CDROM_MEDIA="):
                    if line.endswith("1") and current_dev:
                        print(f"[disc inserted] {current_dev}")
                        drivemanager.scan_drives()
                    current_dev = None
                elif line.startswith("ID_CDROM_MEDIA=") and line.endswith("0") and current_dev:
                    print(f"[disc removed] {current_dev}")
                    tracker.update_status(current_dev, "idle")
                    current_dev = None
        except Exception as e:
            print(f"[discmonitor] error: {e}")

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()