from fastapi import APIRouter, Depends, HTTPException
from .utils.get_systeminfo import get_system_info
from .utils.get_driveinfo import get_drive_info
from .job_tracker import JobTracker
from fastapi.security import HTTPBasicCredentials

router = APIRouter()
job_tracker = JobTracker()

@router.get("/system_info")
def system_info():
    """Retrieve system information such as OS, CPU, Memory, Storage, and GPU details."""
    return get_system_info()

@router.get("/drives")
def list_drives():
    """Retrieve a list of available drives and their status."""
    return get_drive_info()

@router.post("/jobs/start")
def start_job(drive_path: str):
    """Start a new disc ripping job."""
    job_id = job_tracker.start_job(drive_path)
    if job_id is None:
        raise HTTPException(status_code=400, detail="Failed to start job")
    return {"job_id": job_id}

@router.get("/jobs/{job_id}")
def get_job_status(job_id: str):
    """Retrieve the status of a running job."""
    job_status = job_tracker.get_job_status(job_id)
    if job_status is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job_status

@router.delete("/jobs/{job_id}")
def cancel_job(job_id: str):
    """Cancel a running job."""
    success = job_tracker.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to cancel job")
    return {"detail": "Job canceled successfully"}
