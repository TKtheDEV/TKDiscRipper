from dataclasses import dataclass, field
from pathlib import Path
from collections import deque
from typing import Optional
import time
import uuid


@dataclass
class Job:
    job_id: str
    disc_type: str
    drive: str
    disc_label: str
    temp_folder: Path
    output_folder: Path
    pathlock: bool = False
    start_time: float = field(default_factory=time.time)
    steps_total: int = 2
    step: int = 1
    step_description: str = "Initializing"
    step_progress: int = 0
    status: str = "Queued"
    progress: int = 0
    stdout_log: deque = field(default_factory=lambda: deque(maxlen=15))
    runner: Optional["JobRunner"] = None  # Link to running process (defined later)


class JobTracker:
    def __init__(self):
        self.jobs = {}

    def add_job(self, disc_type, drive, disc_label, temp_folder, output_folder) -> Job:
        job_id = str(uuid.uuid4())
        job = Job(
            job_id=job_id,
            disc_type=disc_type,
            drive=drive,
            disc_label=disc_label,
            temp_folder=Path(temp_folder),
            output_folder=Path(output_folder)
        )
        self.jobs[job_id] = job
        return job

    def get_job(self, job_id) -> Optional[Job]:
        return self.jobs.get(job_id)

    def cancel_job(self, job_id) -> bool:
        job = self.jobs.get(job_id)
        if job and job.runner:
            job.runner.cancel()
            job.status = "Cancelled"
            return True
        return False

    def update_status(self, job_id, message: str, step: Optional[int] = None, step_progress: Optional[int] = None):
        job = self.jobs.get(job_id)
        if job:
            job.status = message
            if step is not None:
                job.step = step
            if step_progress is not None:
                job.step_progress = step_progress
                job.progress = int((step_progress + (job.step - 1) * 100) / job.steps_total)
            return True
        return False

job_tracker = JobTracker()