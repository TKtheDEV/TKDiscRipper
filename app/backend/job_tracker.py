import threading
import time
import uuid
from typing import Dict, Optional
import subprocess
import os
from collections import deque

class JobTracker:
    """Tracks disc ripping jobs with additional features like progress, stdout logs, etc."""
    
    def __init__(self):
        self.jobs: Dict[str, Dict] = {}
        self.lock = threading.Lock()

    def start_job(self, drive_path: str, disc_name: str, output_folder: Optional[str] = None) -> str:
        """Starts a new job and returns its unique ID."""
        job_id = str(uuid.uuid4())
        start_time = time.time()

        # Initialize job with basic information
        with self.lock:
            self.jobs[job_id] = {
                "job_id": job_id,
                "disc_name": disc_name,
                "start_time": start_time,
                "elapsed_time": 0,
                "status": "running",
                "progress": 0,  # Initial progress is 0
                "drive": drive_path,
                "output_folder": output_folder,
                "stdout_log": deque(maxlen=15),  # To store the last 15 lines of stdout
            }

        # Start the job in a separate thread
        threading.Thread(target=self._run_job, args=(job_id,)).start()
        return job_id

    def _run_job(self, job_id: str):
        """Simulates a ripping job. This should run the actual rip process and handle output and progress."""
        job = self.jobs.get(job_id)
        if not job:
            return

        # Simulate the ripping process (replace with actual logic for ripping)
        total_steps = 100  # Assume we have 100 steps in the job (for progress tracking)
        
        for step in range(total_steps):
            # Simulate some progress
            time.sleep(0.1)
            progress = int((step + 1) / total_steps * 100)  # Calculate progress percentage
            
            # Update job progress and log output
            self._update_job(job_id, progress, f"Progress: {progress}%")
        
        # Finalize the job status once it's done
        self._update_job(job_id, 100, "Job completed successfully.")

    def _update_job(self, job_id: str, progress: int, stdout: str):
        """Update job's progress and log stdout."""
        with self.lock:
            job = self.jobs.get(job_id)
            if job:
                # Update progress
                job["progress"] = progress
                # Add the stdout log
                job["stdout_log"].append(stdout)
                # Update elapsed time
                job["elapsed_time"] = time.time() - job["start_time"]
                # If progress is 100%, mark job as completed
                if progress == 100:
                    job["status"] = "completed"

    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Returns the status of a given job."""
        with self.lock:
            job = self.jobs.get(job_id)
            if job:
                job["elapsed_time"] = time.time() - job["start_time"]
            return job
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancels an ongoing job."""
        with self.lock:
            job = self.jobs.get(job_id)
            if job and job["status"] == "running":
                # Update job status to canceled
                job["status"] = "canceled"
                return True
        return False

    def get_job_logs(self, job_id: str) -> Optional[deque]:
        """Returns the last 15 lines of stdout for the job."""
        with self.lock:
            job = self.jobs.get(job_id)
            if job:
                return job["stdout_log"]
            return None


# Example usage of the JobTracker:

if __name__ == "__main__":
    tracker = JobTracker()
    
    # Start a job (Simulating disc insert)
    job_id = tracker.start_job("/dev/sr0", "MyDVD", "/home/user/output")
    
    # Check the status after 2 seconds
    time.sleep(2)
    print(tracker.get_job_status(job_id))
    
    # Simulate more time passing
    time.sleep(8)
    print(tracker.get_job_status(job_id))

    # Cancel a job (optional)
    # tracker.cancel_job(job_id)
    # print(tracker.get_job_status(job_id))
