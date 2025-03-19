from fastapi import APIRouter, Depends, HTTPException
from backend.utils.get_driveinfo import get_drive_info
from backend.utils.get_systeminfo import get_system_info
from backend.utils.config_manager import get_config
from backend.job_tracker import JobTracker
from backend.cd import rip_cd
from backend.dvd import rip_dvd
from backend.bluray import rip_bluray
from backend.otherdisc import rip_other
import uuid

router = APIRouter()
tracker = JobTracker()

@router.get("/drives")
def list_drives():
    """List available optical drives."""
    return get_drive_info()

@router.get("/system_info")
def system_info():
    """Retrieve system information."""
    return get_system_info()

@router.post("/jobs/create")
def create_job(drive_path: str, disc_type: str):
    """Create a new ripping job dynamically."""
    job_id = tracker.start_job(drive_path, disc_type)

    return {"job_id": job_id, "status": "Job created"}

@router.get("/jobs/{job_id}")
def get_job_status(job_id: str):
    """Check the status of a job."""
    job = tracker.get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.delete("/jobs/{job_id}")
def cancel_job(job_id: str):
    """Cancel a running job."""
    if tracker.cancel_job(job_id):
        return {"detail": "Job canceled"}
    raise HTTPException(status_code=400, detail="Job not found or cannot be canceled")
