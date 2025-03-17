import subprocess
import os
import time

# List of blacklisted drives
BLACKLISTED_DRIVES = ["/dev/sr1"]

# Handlers for different disc types
HANDLERS = {
    "audio_cd": "cd_handler.py",
    "cd_rom": "data_disc.py",  # CD-ROMs are handled like data discs
    "dvd_video": "dvd_handler.py",
    "blu_ray_video": "bluray_handler.py",
    "data_disc": "data_disc.py",
    "other": "other_disc.py"
}

def get_mount_point(drive):
    """Get the mount point of the drive using lsblk."""
    try:
        result = subprocess.run(['lsblk', '-o', 'MOUNTPOINT', drive],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Split the result and skip the header
        mount_point = result.stdout.strip().split('\n')[1:]  # Skip the header
        if mount_point:
            return mount_point[0]  # Get the first line (actual mount point)
        else:
            return None
    except Exception as e:
        print(f"Error getting mount point for {drive}: {e}")
        return None

def has_folder(drive, folder_name):
    """Check if the disc contains a specific folder (like VIDEO_TS or BDMV)."""
    mount_point = get_mount_point(drive)
    if mount_point:
        folder_path = os.path.join(mount_point, folder_name)
        return os.path.isdir(folder_path)
    return False

def get_disc_type(drive):
    """Detect the type of disc inserted."""
    try:
        # Use blkid to check the filesystem type
        result = subprocess.run(['blkid', '-o', 'value', '-s', 'TYPE', drive],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        filesystem_type = result.stdout.strip().lower()

        # Check for UDF or ISO9660 filesystems (likely a DVD or Blu-ray)
        if filesystem_type in ['udf', 'iso9660']:
            # Check the size of the disc to distinguish between CD, DVD, and Blu-ray
            size_result = subprocess.run(['lsblk', '-bno', 'SIZE', drive], stdout=subprocess.PIPE, text=True)
            disc_size = int(size_result.stdout.strip())

            if disc_size < 1 * 1024 * 1024 * 1024:  # Less than 1GB → Likely a CD-ROM (Data CD)
                return "cd_rom"
            elif 1 * 1024 * 1024 * 1024 <= disc_size <= 25 * 1024 * 1024 * 1024:  # Between 1GB and 25GB → Likely a DVD
                # Check for VIDEO_TS folder for DVD-Video
                return "dvd_video" if has_folder(drive, "VIDEO_TS") else "data_disc"
            elif disc_size > 25 * 1024 * 1024 * 1024:  # Greater than 25GB → Likely Blu-ray
                # Check for BDMV folder for Blu-ray Video
                return "blu_ray_video" if has_folder(drive, "BDMV") else "data_disc"

        # If filesystem is empty (no detected filesystem), likely an Audio CD
        if filesystem_type == '':
            return "audio_cd"
        
        # If no recognizable filesystem or type, return as generic data disc
        return "data_disc"

    except Exception as e:
        print(f"Error detecting disc type: {e}")
        return "other"

def monitor_cdrom():
    """Monitor CD/DVD/Blu-ray drive for insertions and handle accordingly."""
    process = subprocess.Popen(["udevadm", "monitor", "--property"], stdout=subprocess.PIPE, text=True)

    drive = None
    for line in iter(process.stdout.readline, ""):
        line = line.strip()

        if line.startswith("DEVNAME="):  
            drive = line.split("=")[1]

        if "ID_CDROM_MEDIA=1" in line and drive and drive not in BLACKLISTED_DRIVES:
            print(f"🎉 Disc inserted in {drive}")
            time.sleep(3)  # Allow system to stabilize, check mount point after 3 seconds
            disc_type = get_disc_type(drive)
            handler_script = HANDLERS.get(disc_type, "other_disc.py")

            print(f"📀 Detected {disc_type.upper()} - Calling {handler_script}")
            os.system(f"python3 {handler_script} {drive}")

        elif "ID_CDROM_MEDIA=0" in line and drive:
            print(f"💿 Disc ejected from {drive}")

if __name__ == "__main__":
    print("🔍 Monitoring for disc insertions and ejections...")
    monitor_cdrom()
