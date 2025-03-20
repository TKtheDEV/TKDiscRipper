from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from backend.job_tracker import JobTracker
from backend.utils.get_driveinfo import get_drive_info
from backend.utils.get_systeminfo import get_system_info

router = APIRouter()
tracker = JobTracker()

class JobRequest(BaseModel):
    drive_path: str
    disc_type: str

@router.get("/drives")
def list_drives():
    """List available optical drives."""
    return get_drive_info()

@router.get("/system_info")
def system_info():
    """Retrieve system information."""
    return get_system_info()

@router.post("/jobs/create")
def create_job(job: JobRequest):
    """Create a new job."""
    job_id = tracker.start_job(job.drive_path, job.disc_type)
    return {"job_id": job_id, "status": "Job created"}

@router.get("/jobs/{job_id}")
def get_job_status(job_id: str):
    """Retrieve job status."""
    job = tracker.get_job_status(job_id)
    if job:
        return job
    return {"error": "Job not found"}

@router.delete("/jobs/{job_id}")
def cancel_job(job_id: str):
    """Cancel a running job."""
    if tracker.cancel_job(job_id):
        return {"detail": "Job canceled"}
    raise HTTPException(status_code=400, detail="Job not found or cannot be canceled")
