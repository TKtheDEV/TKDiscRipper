import os
import threading
import time
import uuid
from collections import deque
from typing import Dict, Optional

from app.core.drivemanager import drive_manager
from app.core.rippers.cd import CdRipper
from app.core.rippers.dvd import DvdRipper
from app.core.rippers.bluray import BlurayRipper
from app.core.rippers.other import IsoRipper
from app.core.job.api_helpers import update_job

RIPPER_MAP = {
    "audio_cd": CdRipper,
    "dvd_video": DvdRipper,
    "bluray_video": BlurayRipper,
    "cd_rom": IsoRipper,
    "dvd_rom": IsoRipper,
    "bluray_rom": IsoRipper,
    "otherdisc": IsoRipper,
}

class JobTracker:
    def __init__(self):
        self.jobs: Dict[str, Dict] = {}
        self.lock = threading.Lock()
        self.drive_manager = drive_manager

    def start_job(self, drive_path: str, disc_type: str) -> str:
        job_id = str(uuid.uuid4())
        drive_path = os.path.realpath(drive_path)

        if not self.drive_manager.is_available(drive_path):
            raise ValueError(f"Drive {drive_path} is not available.")

        ripper_cls = RIPPER_MAP.get(disc_type)
        if not ripper_cls:
            raise ValueError(f"Unsupported disc type: {disc_type}")

        ripper = ripper_cls(job_id, drive_path)
        self.drive_manager.mark_busy(drive_path, job_id)

        with self.lock:
            self.jobs[job_id] = {
                "job_id": job_id,
                "disc_type": disc_type,
                "drive": drive_path,
                "disc_label": ripper.disc_label,
                "temp_folder": getattr(ripper, "temp_dir", None),
                "output_folder": getattr(ripper, "output_dir", None),
                "start_time": time.time(),
                "operation": "Initializing",
                "status": "Queued for processing",
                "progress": 0,
                "progress_step": 0,
                "stdout_log": deque(maxlen=15)
            }

        threading.Thread(target=self._run_job, args=(job_id, drive_path, disc_type)).start()
        return job_id

    def _run_job(self, job_id: str, drive_path: str, disc_type: str):
        job = self.jobs.get(job_id)
        if not job:
            return

        try:
            ripper_cls = RIPPER_MAP.get(disc_type)
            if not ripper_cls:
                update_job(job_id, log="❌ Unknown disc type", status="failed", progress=100)
                return

            ripper = ripper_cls(job_id, drive_path)
            for log in ripper.rip():
                update_job(job_id, log=log)

            update_job(job_id, status="completed", progress=100, end_time=time.time())
        except Exception as e:
            update_job(job_id, log=f"❌ Error: {e}", status="failed", progress=100, end_time=time.time())
        finally:
            self.drive_manager.mark_free(drive_path)

    def get_job_status(self, job_id: str) -> Optional[Dict]:
        with self.lock:
            job = self.jobs.get(job_id)
            if not job:
                return None

            now = time.time()
            end_time = job.get("end_time")
            job["elapsed_time"] = (end_time or now) - job["start_time"]
            return job


# Singleton
job_tracker = JobTracker()
