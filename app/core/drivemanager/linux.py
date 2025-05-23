import os
import threading
import logging
from typing import List, Dict, Optional
from app.core.config import get_config
from app.core.driveinfo.linux import LinuxDriveInfo

class DriveManager:
    def __init__(self):
        self.lock = threading.Lock()
        self.blacklist = self._load_blacklist()
        self.drive_map: Dict[str, str] = {}  # drive_path -> job_id
        self.provider = LinuxDriveInfo()

    def _load_blacklist(self) -> List[str]:
        config = get_config()
        raw = config.get("Drives", "blacklist", fallback="")
        return [os.path.realpath(d.strip()) for d in raw.split(",") if d.strip()]

    def reload_blacklist(self):
        with self.lock:
            self.blacklist = self._load_blacklist()

    def mark_busy(self, drive_path: str, job_id: str):
        with self.lock:
            path = os.path.realpath(drive_path)
            self.drive_map[path] = job_id
            logging.debug(f"[DriveManager] Marked busy: {path} → {job_id}")

    def mark_free(self, drive_path: str):
        with self.lock:
            path = os.path.realpath(drive_path)
            if path in self.drive_map:
                logging.debug(f"[DriveManager] Freed: {path}")
                del self.drive_map[path]

    def get_job_for_drive(self, drive_path: str) -> Optional[str]:
        with self.lock:
            return self.drive_map.get(os.path.realpath(drive_path))

    def get_drive_for_job(self, job_id: str) -> Optional[str]:
        with self.lock:
            for path, jid in self.drive_map.items():
                if jid == job_id:
                    return path
        return None

    def is_blacklisted(self, drive_path: str) -> bool:
        return os.path.realpath(drive_path) in self.blacklist

    def is_busy(self, drive_path: str) -> bool:
        return os.path.realpath(drive_path) in self.drive_map

    def is_available(self, drive_path: str) -> bool:
        return not self.is_busy(drive_path) and not self.is_blacklisted(drive_path)

    def get_all_drives(self) -> List[Dict]:
        raw_drives = self.provider.get_drive_info()
        enriched = []

        for drive in raw_drives:
            path = os.path.realpath(drive["path"])
            drive["status"] = (
                "blacklisted" if self.is_blacklisted(path)
                else "busy" if self.is_busy(path)
                else "idle"
            )
            drive["job_id"] = self.get_job_for_drive(path)
            enriched.append(drive)

        return enriched

    def find_available_drive(self, desired_type: str) -> Optional[str]:
        capability_order = {
            "cd": ["CD", "DVD", "BD"],
            "dvd": ["DVD", "BD"],
            "bd": ["BD"]
        }
        desired_caps = capability_order.get(desired_type.lower(), [])
        for drive in self.get_all_drives():
            if drive.get("capability") in desired_caps and drive["status"] == "idle":
                return drive["path"]
        logging.warning(f"[DriveManager] No available {desired_type.upper()} drive")
        return None

    def free_drive_by_job(self, job_id: str):
        drive = self.get_drive_for_job(job_id)
        if drive:
            self.mark_free(drive)

# Singleton
drive_manager = DriveManager()
