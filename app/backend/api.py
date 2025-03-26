import subprocess
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
from backend.drive_tracker import get_drive_tracker
from backend.instance import tracker
from backend.utils.get_driveinfo import get_drive_info
from backend.utils.get_systeminfo import get_system_info

router = APIRouter()
drive_tracker = get_drive_tracker()

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

@router.delete("/jobs/{job_id}/cancel")
def cancel_job(job_id: str):
    """Cancel a running job."""
    if tracker.cancel_job(job_id):
        return {"detail": "Job canceled"}
    raise HTTPException(status_code=400, detail="Job not found or cannot be canceled")

@router.delete("/jobs/{job_id}")
def delete_job(job_id: str):
    """
    Remove job metadata and optionally clean up temp folder.
    """
    job = tracker.jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] == "running":
        raise HTTPException(status_code=409, detail="Cannot delete a running job")

    temp = job.get("temp_folder")
    if temp and os.path.exists(temp):
        try:
            import shutil
            shutil.rmtree(temp)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to clean temp dir: {e}")

    del tracker.jobs[job_id]
    return {"detail": f"Job {job_id} deleted."}


@router.get("/jobs")
def list_jobs():
    """
    Returns a summary of all active/running/finished jobs.
    """
    return list(tracker.jobs.values())


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

#Frontend
from backend.utils.get_systeminfo import get_system_info

@router.get("/partial/system", response_class=HTMLResponse)
def partial_system():
    info = get_system_info()
    html = f"""
    <div class="tile" hx-get="/partial/system" hx-trigger="every 5s" hx-swap="outerHTML">
      <h2>🖥️ System Information</h2>
      <ul>
        <li>OS: {info['os_info']}</li>
        <li>CPU: {info['cpu_info']}</li>
        <li>Memory: {info['memory_info']}</li>
        <li>Storage: {info['storage_info']}</li>
      </ul>
    """
    if info.get("gpu_info"):
        html += "<h3>🎮 GPU(s)</h3>"
        for gpu in info["gpu_info"]:
            html += f"""
            <div class="tile" style="margin-top: 0.5rem; background: #f0f4ff;">
              <strong>{gpu['model']}</strong><br>
              Utilization: {gpu['utilization']}<br>
              Temp: {gpu['temperature']}<br>
              Memory: {gpu['free_memory']} free of {gpu['total_memory']}<br>
            </div>
            """
    else:
        html += "<p>No GPUs found.</p>"

    html += "</div>"
    return HTMLResponse(content=html)


from backend.utils.get_driveinfo import get_drive_info

@router.get("/partial/drives", response_class=HTMLResponse)
def partial_drives():
    drives = get_drive_info()
    html = '<div class="tile" hx-get="/partial/drives" hx-trigger="every 5s" hx-swap="outerHTML">'
    html += '<h2>💿 Drives</h2>'
    html += '''
      <button onclick="openDrive('dvd')">🟢 Open drive for DVD</button>
      <button onclick="openDrive('bd')">🔵 Open drive for Blu-ray</button>
      <ul>
    '''
    for d in drives:
        job_link = f'<a href="/jobs/{d["job_id"]}">Job {d["job_id"]}</a>' if d.get("job_id") else ""
        html += f'''
        <li>{d["path"]} — {d["model"]} ({d["capability"]}) — {d["status"]} {job_link}</li>
        '''
    html += '</ul></div>'
    return HTMLResponse(content=html)


from backend.instance import tracker

@router.get("/partial/jobs", response_class=HTMLResponse)
def partial_jobs():
    jobs = list(tracker.jobs.values())

    html = '<div class="tile" hx-get="/partial/jobs" hx-trigger="every 5s" hx-swap="outerHTML">'
    html += '<h2>📝 Jobs</h2>'

    running = [j for j in jobs if j["status"] == "running"]
    finished = [j for j in jobs if j["status"] != "running"]

    if running:
        html += "<h3>▶️ Running</h3>"
        for job in running:
            html += f'''
            <div class="job-card running">
              <strong>{job['disc_label']}</strong><br>
              Progress: {job['progress']}%<br>
              Status: {job['status']}<br>
              <small>Job ID: {job['job_id']}</small><br>
              <form method="post" action="/api/jobs/{job['job_id']}/cancel">
                <button>Cancel</button>
              </form>
            </div>
            '''

    if finished:
        html += "<h3>✅ Completed</h3>"
        for job in finished:
            html += f'''
            <div class="job-card completed">
              <strong>{job['disc_label']}</strong><br>
              Status: {job['status']}<br>
              Progress: {job['progress']}%<br>
              <small>Job ID: {job['job_id']}</small><br>
              <form method="post" action="/api/jobs/{job['job_id']}?_method=DELETE">
                <button>Delete</button>
              </form>
            </div>
            '''

    html += '</div>'
    return HTMLResponse(content=html)
