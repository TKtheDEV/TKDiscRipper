import os
import subprocess
from fastapi import APIRouter, Depends, HTTPException, status, Body, Request, Form
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from backend.job_tracker import job_tracker
from backend.utils.config_manager import get_config
from backend.utils.get_driveinfo import get_drive_info

router = APIRouter()
templates = Jinja2Templates(directory="app/frontend/templates")

# ========================
# ==== JOB MANAGEMENT ====
# ========================

class JobRequest(BaseModel):
    drive_path: str
    disc_type: str

@router.post("/jobs/create")
def create_job(job: JobRequest):
    try:
        job_id = job_tracker.start_job(job.drive_path, job.disc_type)
        return {"job_id": job_id, "status": "Job created"}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.get("/jobs/{job_id}", response_class=HTMLResponse)
def job_detail(job_id: str, request: Request):
    job = job_tracker.get_job_status(job_id)
    if not job:
        return HTMLResponse(f"<h2>Job {job_id} not found</h2>", status_code=404)
    return templates.TemplateResponse("job_detail.html", {"request": request, "job": job})

@router.patch("/jobs/{job_id}")
def patch_job(job_id: str, payload: dict = Body(...)):
    job = job_tracker.jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    editable_fields = [
        "progress", "operation", "status", "log", "disc_label", "final_output",
        "output_folder", "temp_folder", "end_time"
    ]

    updated = []
    for key in editable_fields:
        if key in payload:
            if key == "log":
                job["stdout_log"].append(str(payload["log"]))
            else:
                job[key] = payload[key]
            updated.append(key)

    return {"updated": updated}

@router.delete("/jobs/{job_id}/cancel")
def cancel_job(job_id: str):
    if job_tracker.cancel_job(job_id):
        return {"detail": "Job canceled"}
    raise HTTPException(status_code=400, detail="Job not found or cannot be canceled")

@router.delete("/jobs/{job_id}")
def delete_job(job_id: str):
    job = job_tracker.jobs.get(job_id)
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

    del job_tracker.jobs[job_id]
    return {"detail": f"Job {job_id} deleted."}

@router.get("/jobs")
def list_jobs():
    return list(job_tracker.jobs.values())

@router.get("/jobs/{job_id}/json")
def get_job_json(job_id: str):
    job = job_tracker.get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

# ========================
# ==== DRIVE HANDLING ====
# ========================

@router.get("/drives")
def list_drives():
    return job_tracker.drive_manager.get_all_drives()

@router.get("/drives/occupancy")
def drive_occupancy():
    drives = job_tracker.drive_manager.get_all_drives()
    busy = {d["path"]: d["job_id"] for d in drives if d["status"] == "busy"}
    free = [d["path"] for d in drives if d["status"] == "idle"]
    return {"busy": busy, "free": free}

@router.post("/drives/open")
def open_drive(disc_type: str):
    path = job_tracker.drive_manager.find_available_drive(disc_type)
    if not path:
        return JSONResponse({"error": f"No available {disc_type.upper()} drive"}, status_code=404)

    try:
        subprocess.run(["eject", path], check=True)
        return {"detail": f"Drive {path} opened", "drive": path}
    except subprocess.CalledProcessError as e:
        return JSONResponse({"error": f"Failed to open drive: {str(e)}"}, status_code=500)

@router.post("/drives/reload_blacklist")
def reload_drive_blacklist():
    job_tracker.drive_manager.reload_blacklist()
    return {"detail": "Drive blacklist reloaded"}

# future API (optional):
@router.delete("/drives/by-job/{job_id}")
def api_free_drive(job_id: str):
    job_tracker.drive_manager.free_drive_by_job(job_id)
    return {"detail": f"Freed drive for job {job_id}"}

# ========================
# ==== SYSTEM SETTINGS ===
# ========================

@router.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request):
    config = get_config()
    return templates.TemplateResponse("settings.html", {"request": request, "config": config})

@router.post("/settings")
def update_setting(section: str = Form(...), key: str = Form(...), value: str = Form(...)):
    config = get_config()
    if not config.has_section(section):
        raise HTTPException(400, detail="Invalid section")
    config.set(section, key, value)
    with open("config/TKDiscRipper.conf", "w") as f:
        config.write(f)
    return HTMLResponse(f"""
        <div class='toast'>✅ {section}.{key} updated.</div>
        <script>setTimeout(() => document.querySelector('.toast')?.remove(), 4000);</script>
    """)

# ========================
# ==== PARTIALS / HTMX ===
# ========================

from backend.utils.get_systeminfo import get_system_info

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
    <div class="tile-row" hx-get="/partial/system" hx-trigger="every 5s" hx-swap="outerHTML">
    """

    html += tile("CPU Info", f"""
        <strong title="{cpu['model']}">{cpu['model']}</strong><br>
        {cpu['cores']} Cores / {cpu['threads']} Threads<br>
        Clock: {cpu['frequency']} MHz<br>
        Usage: {cpu['usage']}%<br>
        Temperature: {cpu['temperature']} °C
    """)

    html += tile("Memory", f"""
        <b>RAM used:</b> {fmt_bytes(mem['used'])} / {fmt_bytes(mem['total'])} ({mem['percent']}%)<br>
        <b>Disk used:</b> {fmt_bytes(disk['used'])} / {fmt_bytes(disk['total'])} ({disk['percent']}%)
    """)

    if isinstance(gpus, list):
        for gpu in gpus:
            html += tile("GPU", f"""
                <strong title="{gpu['model']}">{gpu['model']}</strong><br>
                Util: {gpu['utilization']}%<br>
                Temp: {gpu['temperature']}°C<br>
                Power: {gpu['power_draw']}W<br>
                VRAM: {fmt_bytes(gpu['used_memory'])} / {fmt_bytes(gpu['total_memory'])} ({gpu['percent_memory']}%)
            """)

    enc_lines = []
    if hwenc.get("nvenc"):
        enc_lines.append("NVIDIA NVENC: ✔")
    else:
        enc_lines.append("NVIDIA NVENC: ✘")

    if hwenc.get("vce"):
        enc_lines.append("AMD VCE: ✔")
    else:
        enc_lines.append("AMD VCE: ✘")

    if hwenc.get("qsv"):
        enc_lines.append("Intel QSV: ✔")
    else:
        enc_lines.append("Intel QSV: ✘")

    all_codecs = []
    for codec_list in hwenc["encoders"].values():
        all_codecs.extend(codec_list)
    all_codecs = " ".join(sorted(set(all_codecs)))

    html += tile("HWENC", f"""
    {'<br>'.join(enc_lines)}<br><br>
    <strong title=Supported Codecs:>Supported Codecs:</strong><small>{all_codecs}</small>
    """)

    html += tile("OS Info", f"""
        <b>OS:</b> {os_info['os']}<br>
        <b>Version:</b> {os_info['os_version']}<br>
        <b>Kernel:</b> {os_info['kernel']}<br>
        <b>Uptime:</b> {os_info['uptime']}
    """)

    html += "</div>"

    return HTMLResponse(content=html)

# -------------------------------------------------------------------
# DRIVES PARTIAL
# -------------------------------------------------------------------
@router.get("/partials/drives", response_class=HTMLResponse)
def drive_tiles(request: Request):
    drives = job_tracker.drive_manager.get_all_drives()
    job_map = {}
    for d in drives:
        if d["status"] == "busy" and d["job_id"]:
            job = job_tracker.get_job_status(d["job_id"])
            if job:
                job_map[d["path"]] = job

    return templates.TemplateResponse("partials_drives.html", {
        "request": request,
        "drives": drives,
        "job_map": job_map,
    })

'''
    html = """
    <div class="tile-row" hx-get="/partials/drives" hx-trigger="every 5s" hx-swap="outerHTML">
    """

    # Availability Overview Tile
    html += f"""
    <div class="tile">
      <h2>📊 Drive Availability</h2>
      <table style="font-size: 0.9rem; width: 100%; margin-bottom: 0.5rem;">
        <tr><th></th><th>CD</th><th>DVD</th><th>BluRay</th></tr>
        <tr>
          <td>In Use / Total</td>
          <td>{count['cd']['in_use']} / {count['cd']['total']}</td>
          <td>{count['dvd']['in_use']} / {count['dvd']['total']}</td>
          <td>{count['bd']['in_use']} / {count['bd']['total']}</td>
        </tr>
      </table>
      <b>I want to rip...</b><br>
      <button class="drive-control green" onclick="openDrive('cd')">CD</button>
      <button class="drive-control blue" onclick="openDrive('dvd')">DVD</button>
      <button class="drive-control dark" onclick="openDrive('bd')">Blu-ray</button>
    </div>
    """

    # Individual Drive Tiles
    for d in drives:
        job_link = f'<br><small>Job: <a href="/jobs/{d["job_id"]}">{d["job_id"]}</a></small>' if d.get("job_id") else ""
        caps = ", ".join(d.get("capabilities", []))
        html += f"""
        <div class="tile">
          <strong title="{d['model']}">{d['model']}</strong>
          Path: {d['path']}<br>
          Capabilities: {caps}<br>
          Status: {d['status']}{job_link}
        </div>
        """

    html += "</div>"
    return HTMLResponse(content=html)
'''

# -------------------------------------------------------------------
# JOBS PARTIAL
# -------------------------------------------------------------------
@router.get("/partial/jobs", response_class=HTMLResponse)
def partial_jobs():
    jobs = list(job_tracker.jobs.values())

    html = '<div class="tile" hx-get="/partial/jobs" hx-trigger="every 5s" hx-swap="outerHTML">'
    html += '<h2>📝 Jobs</h2>'

    running = [j for j in jobs if j["operation"] != "complete" or j["operation"] != "failed"]
    finished = [j for j in jobs if j["operation"] == "complete"]
    failed = [j for j in jobs if j["operation"] == "failed"]

    if running:
        html += "<h3>▶️ Running</h3>"
        for job in running:
            html += f'''
            <div class="job-card running">
              <strong>{job['disc_label']}</strong><br>
              Progress: {job['progress']}%<br>
              Operation: {job['operation']}<br>
              <small>Job ID: <a href="/jobs/{job["job_id"]}">{job["job_id"]}</a></small><br>
              <form method="post" action="/jobs/{job['job_id']}/cancel">
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
              <small>Job ID: <a href="/jobs/{job["job_id"]}">{job["job_id"]}</a></small><br>
              <form method="post" action="/jobs/{job['job_id']}?_method=DELETE">
                <button>Delete</button>
              </form>
            </div>
            '''

    html += '</div>'

    if failed:
        html += "<h3>❌ Failed</h3>"
        for job in failed:
            html += f'''
            <div class="job-card failed">
              <strong>{job['disc_label']}</strong><br>
              Status: {job['status']}<br>
              Progress: {job['progress']}%<br>
              <small>Job ID: <a href="/jobs/{job["job_id"]}">{job["job_id"]}</a></small><br>
              <form method="post" action="/jobs/{job['job_id']}?_method=DELETE">
                <button>Delete</button>
              </form>
            </div>
            '''

    html += '</div>'
    return HTMLResponse(content=html)


@router.get("/partial/jobs/{job_id}/log", response_class=HTMLResponse)
def job_log_partial(job_id: str):
    job = job_tracker.get_job_status(job_id)
    if not job:
        return HTMLResponse("❌ Job not found", status_code=404)

    log_html = "<pre style='white-space: pre-wrap; font-size: 0.9rem;'>\n"
    for line in job["stdout_log"]:
        log_html += line + "\n"
    log_html += "</pre>"

    return HTMLResponse(log_html)
