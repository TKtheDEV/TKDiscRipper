from typing import List, Optional, Dict
from threading import Lock

class Drive:
    def __init__(self, path: str, model: str, capability: str):
        self.path = path
        self.model = model
        self.capability = capability
        self.status = "idle"  # idle, busy, blacklisted
        self.job_id: Optional[str] = None
        self.disc_label: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "path": self.path,
            "model": self.model,
            "capability": self.capability,
            "status": self.status,
            "job_id": self.job_id,
            "disc_label": self.disc_label
        }

class DriveTracker:
    def __init__(self):
        self._drives: Dict[str, Drive] = {}
        self._lock = Lock()

    def add_or_update_drive(self, path: str, model: str, capability: str, disc_label: Optional[str] = None):
        with self._lock:
            if path not in self._drives:
                self._drives[path] = Drive(path, model, capability)
            self._drives[path].disc_label = disc_label

    def update_status(self, path: str, status: str, job_id: Optional[str] = None):
        with self._lock:
            if path in self._drives:
                self._drives[path].status = status
                self._drives[path].job_id = job_id if status == "busy" else None

    def blacklist(self, path: str):
        with self._lock:
            if path in self._drives:
                self._drives[path].status = "blacklisted"

    def get_all(self) -> List[Drive]:
        with self._lock:
            return list(self._drives.values())

    def reset(self):
        with self._lock:
            self._drives.clear()

drive_tracker = DriveTracker()
