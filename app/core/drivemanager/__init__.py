import platform

if platform.system() == "Linux":
    from app.core.drivemanager.linux import drive_manager as drive_manager
elif platform.system() == "Windows":
    from app.core.drivemanager.windows import drive_manager as drive_manager
elif platform.system() == "Darwin":
    from app.core.drivemanager.macos import drive_manager as drive_manager