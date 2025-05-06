import logging
import subprocess
from fastapi import APIRouter, Request, Depends, Form, Body
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from app.core.job.tracker import job_tracker
from app.core.config import get_config, set_config, get_description, get_descriptions
from app.core.drivemanager import drive_manager
from app.core.templates import templates
from app.core.systeminfo import SystemInfo

router = APIRouter()

@router.get("/jobs/{job_id}")
def job_detail(job_id: str, request: Request):
    job = job_tracker.get_job_status(job_id)
    return templates.TemplateResponse("job_detail.html", {"request": request, "job": job})

@router.get("/jobs/{job_id}/json")
def job_json(job_id: str):
    return job_tracker.get_job_status(job_id)

@router.get("/jobs/{job_id}/progress")
def job_progress_partial(job_id: str, request: Request):
    job = job_tracker.get_job_status(job_id)
    return templates.TemplateResponse("partial_job_progress.html", {"request": request, "job": job})

@router.get("/api/system-info")
def get_system_info():
    info = SystemInfo().get_system_info()
    return info

@router.get("/api/jobs")
def api_get_jobs():
    return JSONResponse(content=list(job_tracker.jobs.values()))

@router.get("/api/drives")
def api_get_drives():
    return JSONResponse(content=drive_manager.get_all_drives())

@router.post("/api/drives/eject")
def eject_drive(request: Request, payload: dict = Body(...)):
    drive = payload.get("drive")
    if not drive:
        return JSONResponse(content={"error": "Missing drive path"}, status_code=400)

    try:
        # Attempt to eject the drive
        subprocess.run(["eject", drive], check=True)

        # Free the drive if it had a job assigned
        job_id = drive_manager.get_job_for_drive(drive)
        if job_id:
            drive_manager.free_drive_by_job(job_id)

        return JSONResponse(content={"detail": f"✅ Ejected {drive}"})
    except subprocess.CalledProcessError as e:
        return JSONResponse(content={"error": f"Failed to eject {drive}: {e}"}, status_code=500)

@router.get("/settings")
def get_settings(request: Request):
    config = get_config()
    descriptions = get_descriptions()
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "config": config,
        "descriptions": descriptions,
        "get_description": get_description,
    })

@router.post("/settings")
def update_setting(
    section: str = Form(...),
    key: str = Form(...),
    value: str = Form(...)
):
    set_config(section=section, option=key, value=value)
    return HTMLResponse(content="<div class='toast'>✅ Setting updated!</div>")

@router.post("/jobs/create")
def create_job_from_api(payload: dict = Body(...)):
    drive = payload.get("drive_path")
    disc_type = payload.get("disc_type")

    if not drive or not disc_type:
        return JSONResponse(content={"error": "Missing drive or disc_type"}, status_code=400)

    try:
        job_id = job_tracker.start_job(drive, disc_type)
        return {"job_id": job_id}
    except Exception as e:
        logging.warning(f"❌ Could not start job for {drive}: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

@router.patch("/jobs/{job_id}")
def patch_job(job_id: str, payload: dict = Body(...)):
    job = job_tracker.jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    with job_tracker.lock:
        for key, value in payload.items():
            if key == "log":
                if "stdout_log" not in job:
                    job["stdout_log"] = deque(maxlen=15)
                job["stdout_log"].append(str(value))
            else:
                job[key] = value
    return {"detail": "✅ Job updated"}
