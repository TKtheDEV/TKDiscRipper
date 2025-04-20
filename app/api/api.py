import logging
from fastapi import APIRouter, Request, Depends, Form, Body
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from app.core.job.tracker import job_tracker
from app.core.config import get_config, set_config, get_description, get_descriptions
from app.core.drive.manager import drive_manager
from app.core.templates import templates

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

@router.get("/partial/system")
def system_info_partial(request: Request):
    from app.core.os.linux_systeminfo import LinuxSystemInfo
    info = LinuxSystemInfo().get_system_info()
    return templates.TemplateResponse("partial_system.html", {"request": request, "system": info})

@router.get("/partial/jobs")
def jobs_partial(request: Request):
    jobs = list(job_tracker.jobs.values())
    return templates.TemplateResponse("partial_jobs.html", {"request": request, "jobs": jobs})

@router.get("/partial/drives")
def drives_partial(request: Request):
    drives = drive_manager.get_all_drives()
    jobs = {j["drive"]: j for j in job_tracker.jobs.values()}
    return templates.TemplateResponse("partial_drives.html", {"request": request, "drives": drives, "job_map": jobs})

@router.post("/drives/open")
def open_drive(disc_type: str = Form(...)):
    drive = drive_manager.find_available_drive(disc_type)
    if not drive:
        return {"error": "No available drive"}
    job_id = job_tracker.start_job(drive, disc_type)
    return {"job": job_id, "drive": drive}

@router.post("/eject")
def eject_drive(drive: str = Form(...)):
    # could be extended later
    return {"detail": f"Eject not yet implemented for {drive}"}

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
