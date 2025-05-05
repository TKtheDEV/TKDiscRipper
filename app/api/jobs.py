from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from app.core.job_tracker import job_tracker
from app.core.rippers import dvd
from app.core.config_manager.config_manager import ConfigManager
import uuid
import asyncio
from pathlib import Path

router = APIRouter()
config = ConfigManager()

class JobCreateRequest(BaseModel):
    disc_type: str  # e.g., "DVD"
    drive: str      # e.g., "/dev/sr0"
    disc_label: str # e.g., "THEMATRIX"

@router.post("/api/jobs/create")
async def create_job(request: JobCreateRequest, background_tasks: BackgroundTasks):
    disc_type = request.disc_type.upper()
    if disc_type not in ["DVD"]:  # add more when implemented
        raise HTTPException(status_code=400, detail="Unsupported disc type")

    job_id = str(uuid.uuid4())

    temp_base = config.get_path("General.tempdirectory", str(Path.home() / "TKDiscRipper" / "temp"))
    temp_folder = temp_base / job_id

    output_base = config.get_path(f"{disc_type}.outputdirectory", str(Path.home() / "TKDiscRipper" / "output" / disc_type))
    output_folder = output_base / request.disc_label

    job = tracker.add_job(
        disc_type=disc_type,
        drive=request.drive,
        disc_label=request.disc_label,
        temp_folder=temp_folder,
        output_folder=output_folder
    )

    async def start_rip():
        if disc_type == "DVD":
            await dvd.start(job)
        else:
            job.status = "Error: Unsupported disc type"

    background_tasks.add_task(start_rip)
    return {"job_id": job.job_id, "status": "queued"}

@router.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    job = tracker.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": job.job_id,
        "disc_type": job.disc_type,
        "drive": job.drive,
        "disc_label": job.disc_label,
        "status": job.status,
        "progress": job.progress,
        "step_description": job.step_description,
        "stdout_log": list(job.stdout_log)
    }

@router.post("/api/jobs/{job_id}/cancel")
async def cancel_job(job_id: str):
    if tracker.cancel_job(job_id):
        return {"job_id": job_id, "status": "cancelled"}
    else:
        raise HTTPException(status_code=404, detail="Unable to cancel job")

@router.get("/api/jobs")
def get_jobs():
    return list(job_tracker.jobs.values())
