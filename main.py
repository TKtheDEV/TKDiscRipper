from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles

import subprocess
import threading
import os
import logging

from app.api.api import router as api_router
from app.api.ws_log import ws_router
from app.core.config import get_config
from app.core.disc_detection import monitor_cdrom
from app.core.job.tracker import job_tracker
from app.core.templates import templates

app = FastAPI(title="TKDiscRipper", version="2.0")
security = HTTPBasic()

app.mount("/static", StaticFiles(directory="app/frontend/static"), name="static")

config = get_config()
USERNAME = config.get("auth", "username")
PASSWORD = config.get("auth", "password")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != USERNAME or credentials.password != PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials

app.include_router(api_router, dependencies=[Depends(authenticate)])
app.include_router(ws_router)

def generate_ssl_cert(cert_file, key_file):
    logging.info("🔑 Generating self-signed SSL certificate and key...")
    subprocess.run(
        [
            "openssl", "req", "-x509", "-newkey", "rsa:2048", "-days", "3650",
            "-nodes", "-keyout", key_file, "-out", cert_file,
            "-subj", "/C=TK/ST=Dev/L=Localhost/O=TKDiscRipper/CN=localhost"
        ],
        check=True
    )
    logging.info("✅ SSL certificate generated.")

@app.on_event("startup")
def startup_event():
    threading.Thread(target=monitor_cdrom, daemon=True).start()

@app.get("/", dependencies=[Depends(authenticate)])
def dashboard(request: Request):
    jobs = list(job_tracker.jobs.values())
    return templates.TemplateResponse("dashboard.html", {"request": request, "jobs": jobs})

if __name__ == "__main__":
    cert_file = "config/server.crt"
    key_file = "config/server.key"
    if not os.path.exists(cert_file) or not os.path.exists(key_file):
        generate_ssl_cert(cert_file, key_file)
    import uvicorn
    uvicorn.run(app, host="::", port=8000, ssl_keyfile=key_file, ssl_certfile=cert_file)
