from fastapi import FastAPI, Depends, HTTPException, status
import uvicorn
from .backend.api import router as api_router
from .backend.utils.config_manager import get_config
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import ssl
import os
import logging
import subprocess

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
    logging.info("Generating self-signed SSL certificate and key...")
    try:
        # Use openssl to generate the certificate and key (no passphrase)
        subprocess.run(
            [
                "openssl", "req", "-x509", "-newkey", "rsa:2048", "-days", "3650",
                "-nodes", "-keyout", key_file, "-out", cert_file,
                "-subj", "/C=TK/ST=GitHub/L=TKtheDEV/O=TKDiscRipper/CN=localhost"
            ],
            check=True
        )
        logging.info("SSL certificate and key generated successfully.")
    except subprocess.CalledProcessError as e:
        logging.error("Error generating SSL certificate and key: %s", e)
        raise RuntimeError("SSL certificate generation failed.")

if __name__ == "__main__":
    cert_file = "config/server.crt"
    key_file = "config/server.key"
    
    # Check if the SSL certificate and key exist, if not, generate them
    if not os.path.exists(cert_file) or not os.path.exists(key_file):
        generate_ssl_cert(cert_file, key_file)
    
    # Run the app with SSL
    uvicorn.run(app, host="::", port=8000, ssl_keyfile=key_file, ssl_certfile=cert_file)