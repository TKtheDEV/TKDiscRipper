import threading
import os
import logging
from typing import Dict, Optional, List
from backend.utils.config_manager import get_config
from backend.utils.get_driveinfo import get_drive_info


class DriveTracker:
    """Tracks which drives are in use, manages job association and blacklist, and matches capabilities."""

    def __init__(self):
        self.lock = threading.Lock()
        self.drive_map: Dict[str, str] = {}  # drive_path -> job_id
        self.blacklist: List[str] = self._load_blacklist()

    def _load_blacklist(self) -> List[str]:
        config = get_config()
        raw = config.get("Drives", "blacklist", fallback="")
        return [os.path.realpath(d.strip()) for d in raw.split(",") if d.strip()]

    def reload_blacklist(self):
        with self.lock:
            self.blacklist = self._load_blacklist()

    def mark_busy(self, drive_path: str, job_id: str):
        drive_path = os.path.realpath(drive_path)
        with self.lock:
            logging.debug(f"Marking {drive_path} as busy for job {job_id}")
            self.drive_map[drive_path] = job_id

    def mark_free(self, drive_path: str):
        drive_path = os.path.realpath(drive_path)
        with self.lock:
            logging.debug(f"Marking {drive_path} as free")
            self.drive_map.pop(drive_path, None)

    def is_busy(self, drive_path: str) -> bool:
        drive_path = os.path.realpath(drive_path)
        with self.lock:
            return drive_path in self.drive_map

    def is_blacklisted(self, drive_path: str) -> bool:
        drive_path = os.path.realpath(drive_path)
        return drive_path in self.blacklist

    def is_available(self, drive_path: str) -> bool:
        return not self.is_blacklisted(drive_path) and not self.is_busy(drive_path)

    def get_job_for_drive(self, drive_path: str) -> Optional[str]:
        drive_path = os.path.realpath(drive_path)
        with self.lock:
            return self.drive_map.get(drive_path)

    def get_drive_for_job(self, job_id: str) -> Optional[str]:
        with self.lock:
            for drive, jid in self.drive_map.items():
                if jid == job_id:
                    return drive
            return None

    def get_busy_drives(self) -> Dict[str, str]:
        with self.lock:
            return dict(self.drive_map)

    def get_free_drives(self, all_known_drives: List[str]) -> List[str]:
        with self.lock:
            return [
                os.path.realpath(d) for d in all_known_drives
                if d not in self.drive_map and d not in self.blacklist
            ]

    def find_available_drive(self, desired_type: str) -> Optional[str]:
        """
        Finds a free, non-blacklisted drive that supports the desired disc type.
        Uses a simplified tier model (BD > DVD > CD).
        """
        capability_order = {
            "cd": ["CD", "DVD", "BD"],
            "dvd": ["DVD", "BD"],
            "bd": ["BD"]
        }

        desired_levels = capability_order.get(desired_type.lower(), [])
        all_drives = get_drive_info()

        for level in desired_levels:
            for drive in all_drives:
                path = os.path.realpath(drive["path"])
                if (
                    drive.get("capability") == level
                    and not self.is_blacklisted(path)
                    and not self.is_busy(path)
                ):
                    return path
        logging.warning(f"[DriveTracker] No available drive for {desired_type.upper()}")
        return None


# ✅ Singleton instance
_drive_tracker_instance = DriveTracker()

def get_drive_tracker() -> DriveTracker:
    return _drive_tracker_instance
