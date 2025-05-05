import platform

if platform.system() == "Linux":
    from app.core.disc_detection.linux import monitor_cdrom
elif platform.system() == "Windows":
    from app.core.disc_detection.windows import monitor_cdrom
elif platform.system() == "Darwin":
    from app.core.disc_detection.macos import monitor_cdrom