import subprocess
import logging
import os
import time
import requests
from requests.auth import HTTPBasicAuth
from app.core.config import get_config
from app.core.drivemanager import drive_manager

# API endpoint
API_URL = "https://[::1]:8000"

# Load credentials from config
config = get_config()
USERNAME = config.get("auth", "username")
PASSWORD = config.get("auth", "password")

# Mapping filesystem + folder detection to disc type
DISC_TYPES = {
    "audio_cd": "audio_cd",
    "cd_rom": "cd_rom",
    "dvd_video": "dvd_video",
    "dvd_rom": "dvd_rom",
    "blu_ray_video": "bluray_video",
    "blu_ray_rom": "blu_ray_rom"
}

def get_disc_type(drive):
    """Detect the type of disc inserted."""
    try:
        result = subprocess.run(['blkid', '-o', 'value', '-s', 'TYPE', drive], stdout=subprocess.PIPE, text=True)
        filesystem_type = result.stdout.strip().lower()

        size_result = subprocess.run(['lsblk', '-bno', 'SIZE', drive], stdout=subprocess.PIPE, text=True)
        disc_size = int(size_result.stdout.strip())

        if filesystem_type in ['udf', 'iso9660']:
            if disc_size < 1 * 1024 * 1024 * 1024:
                return "cd_rom"
            elif 1 * 1024 * 1024 * 1024 <= disc_size <= 25 * 1024 * 1024 * 1024:
                return "dvd_video" if has_folder(drive, "VIDEO_TS") else "dvd_rom"
            elif disc_size > 25 * 1024 * 1024 * 1024:
                return "blu_ray_video" if has_folder(drive, "BDMV") else "blu_ray_rom"

        if filesystem_type == '':
            return "audio_cd"

        else:
            return "other_disc"

    except Exception as e:
        logging.error(f"Error detecting disc type for {drive}: {e}")
        return "other"

def has_folder(drive, folder_name):
    """Check if the disc contains a specific folder."""
    mount_point = get_mount_point(drive)
    if mount_point:
        return os.path.isdir(os.path.join(mount_point, folder_name))
    return False

def get_mount_point(drive):
    """Get the mount point of the drive."""
    try:
        result = subprocess.run(['lsblk', '-o', 'MOUNTPOINT', drive], stdout=subprocess.PIPE, text=True)
        mount_point = result.stdout.strip().split('\n')[1:]
        return mount_point[0] if mount_point else None
    except Exception as e:
        logging.error(f"Error getting mount point for {drive}: {e}")
        return None

def start_ripping(drive, disc_type):
    """Start a ripping job via API. Let the backend decide availability."""
    job_type = DISC_TYPES.get(disc_type, "otherdisc")

    try:
        response = requests.post(
            f"{API_URL}/jobs/create",
            json={"drive_path": drive, "disc_type": job_type},
            auth=HTTPBasicAuth(USERNAME, PASSWORD),
            verify=False
        )
        if response.status_code == 200:
            logging.info(f"✅ Started job: {response.json()}")
        else:
            logging.warning(f"❌ Could not start job for {drive}: {response.text}")
    except Exception as e:
        logging.error(f"❌ Error calling API to start job: {e}")

def monitor_cdrom():
    """Monitors for disc insertions and starts ripping via backend API."""
    logging.info("🔍 Monitoring for disc insertions...")

    process = subprocess.Popen(["udevadm", "monitor", "--property"], stdout=subprocess.PIPE, text=True)
    drive = None

    for line in iter(process.stdout.readline, ""):
        line = line.strip()

        if line.startswith("DEVNAME="):
            drive = line.split("=")[1]

        if "ID_CDROM_MEDIA=1" in line and drive:
            logging.info(f"📥 Disc inserted in {drive}")
            time.sleep(5)  # debounce
            disc_type = get_disc_type(drive)
            logging.info(f"📀 Detected {disc_type.upper()} in {drive}")
            start_ripping(drive, disc_type)

        elif "ID_CDROM_MEDIA=0" in line and drive:
            logging.info(f"💿 Disc ejected from {drive}")
            try:
                # Optional: inform backend to free the drive
                requests.delete(
                    f"{API_URL}/jobs/{drive}",
                    auth=HTTPBasicAuth(USERNAME, PASSWORD),
                    verify=False
                )
            except Exception as e:
                logging.warning(f"⚠️ Could not notify backend of eject: {e}")
