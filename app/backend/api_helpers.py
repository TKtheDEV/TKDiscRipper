import requests
from requests.auth import HTTPBasicAuth
import urllib3
from backend.utils.config_manager import get_config

# Disable SSL warnings (since we're using localhost self-signed)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

config = get_config()
API_URL = "https://[::1]:8000"
AUTH = HTTPBasicAuth(config.get("auth", "username"), config.get("auth", "password"))

def get_job(job_id: str) -> dict:
    """
    Get a job's current state from the API.
    """
    r = requests.get(f"{API_URL}/jobs/{job_id}", auth=AUTH, timeout=5, verify=False)
    r.raise_for_status()
    return r.json()

def update_job(job_id: str, **kwargs):
    """
    Patch a job via the API.
    - Use log=... to append a line to the stdout_log.
    - Use any other fields to update metadata (status, progress, etc).
    """
    payload = dict(kwargs)
    r = requests.patch(f"{API_URL}/jobs/{job_id}", json=payload, auth=AUTH, timeout=5, verify=False)

    if not r.ok:
        raise RuntimeError(f"Failed to update job {job_id}: {r.status_code} {r.text}")
