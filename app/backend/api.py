import subprocess
from fastapi import APIRouter, Depends, HTTPException, status
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
# -------------------------------------------------------------------
# SYSTEM INFO PARTIAL
# -------------------------------------------------------------------
@router.get("/partial/system", response_class=HTMLResponse)
def partial_system():
    info = get_system_info()

    os_info = info["os_info"]
    cpu = info["cpu_info"]
    mem = info["memory_info"]
    disk = info["storage_info"]
    gpus = info["gpu_info"]
    hwenc = info["hwenc_info"]

    def fmt_bytes(b):
        return f"{round(b / 1024 / 1024 / 1024, 1)} GB"

    def tile(title, content):
        return f"""<div class="tile"><h2>{title}</h2>{content}</div>"""

    html = """
    <div class="tile-row" hx-get="/api/partial/system" hx-trigger="every 5s" hx-swap="outerHTML">
    """

    html += tile("CPU Info", f"""
        {cpu['model']}<br>
        {cpu['cores']} Cores / {cpu['threads']} Threads<br>
        Clock: {cpu['frequency']} MHz<br>
        Usage: {cpu['usage']}%<br>
        Temperature: {cpu['temperature']} °C
    """)

    html += tile("RAM Info", f"""
        Total: {fmt_bytes(mem['total'])}<br>
        Used: {fmt_bytes(mem['used'])} ({mem['percent']}%)
    """)

    if isinstance(gpus, list):
        for gpu in gpus:
            html += tile("GPU", f"""
                <strong>{gpu['model']}</strong><br>
                Util: {gpu['utilization']}%<br>
                Temp: {gpu['temperature']}°C<br>
                Power: {gpu['power_draw']}W<br>
                VRAM: {fmt_bytes(gpu['used_memory'])} / {fmt_bytes(gpu['total_memory'])} ({gpu['percent_memory']}%)
            """)

    html += tile("HWENC", "<br>".join([
        f"<b>{k.upper()}</b>: ✅ <small>({', '.join(hwenc['encoders'].get(k, []))})</small>" if hwenc.get(k)
        else f"<b>{k.upper()}</b>: ❌"
        for k in ["nvenc", "qsv", "vce"]
    ]))

    html += tile("Storage Info", f"""
        Total: {fmt_bytes(disk['total'])}<br>
        Used: {fmt_bytes(disk['used'])} ({disk['percent']}%)
    """)

    html += tile("OS Info", f"""
        OS: {os_info['os']} {os_info['os_version']}<br>
        Kernel: {os_info['kernel']}<br>
        Uptime: {os_info['uptime']}
    """)

    html += "</div>"

    return HTMLResponse(content=html)

# -------------------------------------------------------------------
# DRIVES PARTIAL
# -------------------------------------------------------------------
@router.get("/partial/drives", response_class=HTMLResponse)
def partial_drives():
    drives = get_drive_info()
    html = '<div class="tile" hx-get="/api/partial/drives" hx-trigger="every 5s" hx-swap="outerHTML">'
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

# -------------------------------------------------------------------
# JOBS PARTIAL
# -------------------------------------------------------------------
@router.get("/partial/jobs", response_class=HTMLResponse)
def partial_jobs():
    jobs = list(tracker.jobs.values())

    html = '<div class="tile" hx-get="/api/partial/jobs" hx-trigger="every 5s" hx-swap="outerHTML">'
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