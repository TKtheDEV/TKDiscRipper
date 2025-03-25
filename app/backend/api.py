import subprocess
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from backend.drive_tracker import get_drive_tracker
from backend.job_tracker import JobTracker
from backend.utils.get_driveinfo import get_drive_info
from backend.utils.get_systeminfo import get_system_info

router = APIRouter()
drive_tracker = get_drive_tracker()
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
    try:
        job_id = tracker.start_job(job.drive_path, job.disc_type)
        return {"job_id": job_id, "status": "Job created"}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

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

#DRIVE SECTION

@router.get("/drives/occupancy")
def drive_occupancy():
    """Show which drives are busy or free, with associated job IDs."""
    all_drives = [d["path"] for d in get_drive_info()]
    busy = drive_tracker.get_busy_drives()
    free = drive_tracker.get_free_drives(all_drives)
    return {"busy": busy, "free": free}

@router.post("/drives/reload_blacklist")
def reload_drive_blacklist():
    """Reload drive blacklist from the config file."""
    drive_tracker.reload_blacklist()
    return {"detail": "Drive blacklist reloaded"}

@router.post("/drives/open")
def open_drive(disc_type: str):
    """
    Ejects an available drive (by type) for the user to insert a disc.
    Accepts: cd, dvd, bluray
    """
    drive = drive_tracker.find_available_drive(disc_type)
    if not drive:
        return JSONResponse({"error": f"No available {disc_type.upper()} drive"}, status_code=404)

    try:
        subprocess.run(["eject", drive], check=True)
        return {"detail": f"Drive {drive} opened for {disc_type.upper()}", "drive": drive}
    except subprocess.CalledProcessError as e:
        return JSONResponse({"error": f"Failed to open drive: {str(e)}"}, status_code=500)

