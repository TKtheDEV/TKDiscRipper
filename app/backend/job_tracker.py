import threading
import time
import uuid
from collections import deque
from typing import Dict, Optional
from backend.drive_tracker import get_drive_tracker
from backend.dvd import DvdRipper
from backend.cd import CdRipper
from backend.bluray import BlurayRipper
from backend.utils.config_manager import get_config

class JobTracker:
    """Tracks disc ripping jobs with real-time progress and logs."""

    def __init__(self):
        self.jobs: Dict[str, Dict] = {}
        self.lock = threading.Lock()
        self.drive_tracker = get_drive_tracker()

    def start_job(self, drive_path: str, disc_type: str) -> str:
        """Creates a new job and starts the ripping process."""
        if not self.drive_tracker.is_available(drive_path):
            raise ValueError(f"Drive {drive_path} is not available.")
        job_id = str(uuid.uuid4())
        config = get_config()
        output_folder = config.get("paths", "output_dir", fallback="output")

        with self.lock:
            self.jobs[job_id] = {
                "job_id": job_id,
                "disc_type": disc_type,
                "drive": drive_path,
                "output_folder": output_folder,
                "start_time": time.time(),
                "elapsed_time": 0,
                "progress": 0,
                "status": "running",
                "stdout_log": deque(maxlen=15),  # ✅ Stores last 15 log lines
            }

        print("Drive Path:", drive_path)
        self.drive_tracker.mark_busy(drive_path, job_id)
        threading.Thread(target=self._run_job, args=(job_id, drive_path, disc_type)).start()
        return job_id

    def _run_job(self, job_id: str, drive_path: str, disc_type: str):
        """Runs the ripping job and captures logs."""
        job = self.jobs.get(job_id)
        if not job:
            return

        try:
            ripper = None

            # ✅ Choose correct ripper based on disc type
            if disc_type in ["dvd", "dvd_video"]:
                ripper = DvdRipper(drive_path, job_id)
                rip_logs = ripper.rip_dvd()
            elif disc_type in ["cd", "audio_cd"]:
                ripper = CdRipper(drive_path, job_id)
                rip_logs = ripper.rip_cd()
            elif disc_type in ["bluray", "blu_ray_video"]:
                ripper = BlurayRipper(drive_path, job_id)
                rip_logs = ripper.rip_bluray()
            else:
                self._update_job(job_id, "❌ Unknown disc type", failed=True)
                return

            # ✅ Capture logs in real-time
            for log in rip_logs:
                with self.lock:
                    job["stdout_log"].append(log.strip())  # ✅ Append logs
                    job["elapsed_time"] = time.time() - job["start_time"]

            self._update_job(job_id, "✅ Ripping completed successfully.", completed=True)

        except Exception as e:
            self._update_job(job_id, f"❌ Error: {e}", failed=True)

    def _update_job(self, job_id: str, log_message: str, completed: bool = False, failed: bool = False):
        """Updates job logs and status."""
        with self.lock:
            job = self.jobs.get(job_id)
            if not job:
                return

            job["stdout_log"].append(log_message)
            job["elapsed_time"] = time.time() - job["start_time"]

            if completed:
                job["status"] = "completed"
            elif failed:
                job["status"] = "failed"

            if completed or failed:
                self.drive_tracker.mark_free(job["drive"])

    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Returns the status of a given job."""
        with self.lock:
            job = self.jobs.get(job_id)
            if job:
                job["elapsed_time"] = time.time() - job["start_time"]
                return job
        return None
