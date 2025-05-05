from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles

from pathlib import Path
import logging

from app.api.jobs import router as api_router
from app.api.ws_log import router as ws_router
from app.api.system_info import router as system_router
from app.api.drives import router as drives_router
from app.core.config_manager.config_manager import ConfigManager
from app.core.job_tracker import JobTracker
from app.core.templates import templates
from app.core.discmonitor import monitor_disc_events

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta

import threading
import time
from app.core.drivemanager import linux as drivemanager

app = FastAPI(title="TKDiscRipper", version="2.0")
security = HTTPBasic()

# Serve static assets
app.mount("/static", StaticFiles(directory="app/frontend/static"), name="static")

# Load config
config = ConfigManager()
USERNAME = config.get("auth.username", "admin")
PASSWORD = config.get("auth.password", "admin")

# Basic auth middleware
def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != USERNAME or credentials.password != PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

# Include routers
app.include_router(api_router, dependencies=[Depends(authenticate)])
app.include_router(ws_router)
app.include_router(system_router)
app.include_router(drives_router)

# Template routes
job_tracker = JobTracker()

@app.get("/", dependencies=[Depends(authenticate)])
def dashboard(request: Request):
    jobs = list(job_tracker.jobs.values())
    return templates.TemplateResponse("dashboard.html", {"request": request, "jobs": jobs})

@app.get("/job/{job_id}", dependencies=[Depends(authenticate)])
def job_detail(job_id: str, request: Request):
    job = job_tracker.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return templates.TemplateResponse("job_detail.html", {"request": request, "job": job})

@app.get("/settings", dependencies=[Depends(authenticate)])
def settings_page(request: Request):
    return templates.TemplateResponse("settings.html", {"request": request})

# Polling drive scanner
def poll_drives(interval=5):
    while True:
        drivemanager.scan_drives()
        time.sleep(interval)

# Start background monitoring and scanning
@app.on_event("startup")
def start_disc_monitor():
    threading.Thread(target=poll_drives, daemon=True).start()
    monitor_disc_events()

# SSL cert generator
def generate_ssl_cert(cert_file: Path, key_file: Path):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u"TK"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"Dev"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, u"Localhost"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"TKDiscRipper"),
        x509.NameAttribute(NameOID.COMMON_NAME, u"localhost"),
    ])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=3650))
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName(u"localhost")]),
            critical=False
        )
        .sign(key, hashes.SHA256())
    )
    cert_file.parent.mkdir(parents=True, exist_ok=True)
    key_file.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption()
        )
    )
    cert_file.write_bytes(cert.public_bytes(serialization.Encoding.PEM))

# Entrypoint
if __name__ == "__main__":
    import uvicorn

    cert_file = Path.home() / "TKDR" / "config" / "TKDR.crt"
    key_file = Path.home() / "TKDR" / "config" / "TKDR.key"

    if not cert_file.exists() or not key_file.exists():
        generate_ssl_cert(cert_file, key_file)

    uvicorn.run(
        app,
        host="::",
        port=8000,
        ssl_certfile=str(cert_file),
        ssl_keyfile=str(key_file)
    )
