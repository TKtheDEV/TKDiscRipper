import subprocess
import logging
import os
import time
import requests
from requests.auth import HTTPBasicAuth
from .config_manager import get_config

# API endpoint
API_URL = "https://[::1]:8000"

# Load credentials from config
config = get_config()
USERNAME = config.get("auth", "username")
PASSWORD = config.get("auth", "password")

# Blacklisted drives
BLACKLISTED_DRIVES = ["/dev/sr7"]
active_jobs = set()  # ✅ Tracks ongoing jobs to prevent duplicates

DISC_TYPES = {
    "audio_cd": "audio_cd",
    "cd_rom": "otherdisc",
    "dvd_video": "dvd_video",
    "dvd_rom": "otherdisc",
    "blu_ray_video": "bluray_video",
    "blu_ray_rom": "otherdisc"
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

        return "other"
    except Exception as e:
        print(f"Error detecting disc type: {e}")
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
        print(f"Error getting mount point for {drive}: {e}")
        return None

def start_ripping(drive, disc_type):
    """Start a ripping job, ensuring no duplicate jobs start."""
    job_type = DISC_TYPES.get(disc_type, "otherdisc")

    if drive in active_jobs:  # ✅ Prevent duplicate jobs
        logging.info(f"⚠️ Job for {drive} is already running, skipping duplicate.")
        return

    active_jobs.add(drive)  # ✅ Mark drive as active

    try:
        response = requests.post(
            f"{API_URL}/jobs/create",
            json={"drive_path": drive, "disc_type": job_type},
            auth=HTTPBasicAuth(USERNAME, PASSWORD),  # Send authentication
            verify=False  # Disable SSL verification (Optional)
        )
        if response.status_code == 200:
            print(f"✅ Started job: {response.json()}")
        else:
            print(f"❌ Failed to start job: {response.text}")
    except Exception as e:
        print(f"❌ Error calling API: {e}")

def monitor_cdrom():
    """Monitors for disc insertions and starts ripping, preventing duplicates."""
    logging.info("🔍 Monitoring for disc insertions...")

    process = subprocess.Popen(["udevadm", "monitor", "--property"], stdout=subprocess.PIPE, text=True)
    drive = None

    for line in iter(process.stdout.readline, ""):
        line = line.strip()
        
        if line.startswith("DEVNAME="):
            drive = line.split("=")[1]

        if "ID_CDROM_MEDIA=1" in line and drive and drive not in BLACKLISTED_DRIVES:
            if drive in active_jobs:
                continue  # ✅ Ignore duplicate event
            logging.info(f"🎉 Disc inserted in {drive}")
            time.sleep(2)  # ✅ Reduce rapid event firing
            disc_type = get_disc_type(drive)
            logging.info(f"📀 Detected {disc_type.upper()} - Starting job")
            start_ripping(drive, disc_type)

        elif "ID_CDROM_MEDIA=0" in line and drive:
            logging.info(f"💿 Disc ejected from {drive}")
            active_jobs.discard(drive)  # ✅ Free the drive for future jobs

if __name__ == "__main__":
    print("🔍 Monitoring for disc insertions and ejections...")
    monitor_cdrom()
