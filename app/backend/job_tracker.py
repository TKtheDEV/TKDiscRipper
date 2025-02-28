import threading
import time
import uuid
from typing import Dict, Optional

class JobTracker:
    """Tracks disc ripping jobs."""
    def __init__(self):
        self.jobs: Dict[str, Dict] = {}
        self.lock = threading.Lock()
    
    def start_job(self, drive_path: str) -> str:
        """Starts a new job and returns its unique ID."""
        job_id = str(uuid.uuid4())
        start_time = time.time()
        
        with self.lock:
            self.jobs[job_id] = {
                "drive_path": drive_path,
                "start_time": start_time,
                "elapsed_time": 0,
                "status": "running"
            }
        
        threading.Thread(target=self._run_job, args=(job_id,)).start()
        return job_id
    
    def _run_job(self, job_id: str):
        """Simulates a ripping job."""
        time.sleep(10)  # Simulate ripping process
        with self.lock:
            if job_id in self.jobs:
                self.jobs[job_id]["status"] = "completed"
    
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
            if job_id in self.jobs and self.jobs[job_id]["status"] == "running":
                self.jobs[job_id]["status"] = "canceled"
                return True
        return False

if __name__ == "__main__":
    tracker = JobTracker()
    job_id = tracker.start_job("/dev/sr0")
    time.sleep(2)
    print(tracker.get_job_status(job_id))
    time.sleep(10)
    print(tracker.get_job_status(job_id))
