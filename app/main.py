from fastapi import FastAPI, Depends, HTTPException, status
import uvicorn
import threading
import os
import logging
import subprocess
from backend.api import router as api_router
from backend.utils.config_manager import get_config
from backend.utils.disc_detection import monitor_cdrom
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials

app = FastAPI(title="TKDiscRipper", version="1.0")
security = HTTPBasic()

# Load config for credentials
config = get_config()
USERNAME = config.get("auth", "username")
PASSWORD = config.get("auth", "password")

# Middleware for CORS (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency for authentication
def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != USERNAME or credentials.password != PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials

# Include API routes
app.include_router(api_router, dependencies=[Depends(authenticate)])

def generate_ssl_cert(cert_file, key_file):
    """Generate a self-signed SSL certificate and key if they don't exist."""
    logging.info("🔑 Generating self-signed SSL certificate and key...")
    try:
        subprocess.run(
            [
                "openssl", "req", "-x509", "-newkey", "rsa:2048", "-days", "3650",
                "-nodes", "-keyout", key_file, "-out", cert_file,
                "-subj", "/C=TK/ST=GitHub/L=TKtheDEV/O=TKDiscRipper/CN=localhost"
            ],
            check=True
        )
        logging.info("✅ SSL certificate generated successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Error generating SSL certificate: {e}")
        raise RuntimeError("SSL certificate generation failed.")

# Function to start disc detection in a background thread
def start_disc_detection():
    logging.info("🔍 Starting disc detection service...")
    threading.Thread(target=monitor_cdrom, daemon=True).start()

# Startup event to launch disc detection
@app.on_event("startup")
def startup_event():
    start_disc_detection()

if __name__ == "__main__":
    cert_file = "config/server.crt"
    key_file = "config/server.key"
    
    # Check if SSL certificate exists, if not, generate it
    if not os.path.exists(cert_file) or not os.path.exists(key_file):
        generate_ssl_cert(cert_file, key_file)
    
    # Run the app with SSL
    uvicorn.run(app, host="::", port=8000, ssl_keyfile=key_file, ssl_certfile=cert_file)
