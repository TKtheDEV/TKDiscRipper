import threading
import time
import uuid
import subprocess
from collections import deque
from typing import Dict, Optional
from backend.utils.config_manager import get_config
from backend.cd import rip_cd
from backend.dvd import rip_dvd
from backend.bluray import rip_bluray
from backend.otherdisc import rip_other

class JobTracker:
    """Tracks disc ripping jobs with real-time progress, logs, and API control."""

    def __init__(self):
        self.jobs: Dict[str, Dict] = {}
        self.lock = threading.Lock()

    def start_job(self, drive_path: str, disc_type: str) -> str:
        """Creates a new job and starts the actual ripping process."""
        job_id = str(uuid.uuid4())

        # Get output directory from config
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
                "stdout_log": deque(maxlen=50),  # Store last 50 log lines
                "process": None,  # Store the running subprocess for cancellation
            }

        threading.Thread(target=self._run_job, args=(job_id, drive_path, disc_type)).start()
        return job_id

    def _run_job(self, job_id: str, drive_path: str, disc_type: str):
        """Executes the actual ripping process with real-time logging."""
        job = self.jobs.get(job_id)
        if not job:
            return

        # Get the correct ripping function and pass the job_id
        rip_function = {
            "audio_cd": rip_cd,
            "dvd_video": rip_dvd,
            "blu_ray_video": rip_bluray,
        }.get(disc_type, rip_other)

        try:
            # Start the ripping process (passing job_id)
            process = rip_function(drive_path, job_id)

            # Store the process for potential cancellation
            with self.lock:
                job["process"] = process

            # Capture real-time logs and update progress
            for line in iter(process.stdout.readline, ""):
                line = line.strip()
                if not line:
                    continue

                self._update_job(job_id, line)

            # Wait for process completion
            process.wait()

            # Check exit code
            if process.returncode == 0:
                self._update_job(job_id, "✅ Ripping completed successfully.", completed=True)
            else:
                self._update_job(job_id, f"❌ Ripping failed (Exit Code: {process.returncode})", failed=True)

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

    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Returns the status of a given job."""
        with self.lock:
            job = self.jobs.get(job_id)
            if job:
                job["elapsed_time"] = time.time() - job["start_time"]
            return job

    def cancel_job(self, job_id: str) -> bool:
        """Cancels a running job."""
        with self.lock:
            job = self.jobs.get(job_id)
            if job and job["status"] == "running":
                # Terminate the process if it's running
                process = job.get("process")
                if process and process.poll() is None:  # Process is still running
                    process.terminate()
                    process.wait()
                    job["status"] = "canceled"
                    self._update_job(job_id, "❌ Job canceled.")
                    return True
        return False

    def get_job_logs(self, job_id: str) -> Optional[deque]:
        """Returns the last 50 lines of stdout for the job."""
        with self.lock:
            job = self.jobs.get(job_id)
            if job:
                return list(job["stdout_log"])
            return None
