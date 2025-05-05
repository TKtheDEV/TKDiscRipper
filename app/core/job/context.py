from app.core.job.api_helpers import update_job

class JobContext:
    """
    Encapsulates all updates to a job: logs, progress, phase, etc.
    Cleanly separates job logic from system interaction.
    """
    def __init__(self, job_id: str):
        self.job_id = job_id

    def log(self, msg: str):
        update_job(self.job_id, log=msg)

    def set_progress(self, **kwargs):
        update_job(self.job_id, **kwargs)
