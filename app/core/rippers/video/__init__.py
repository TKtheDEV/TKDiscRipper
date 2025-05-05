import platform

if platform.system() == "Linux":
    from app.core.rippers.video.linux import VideoRipper
elif platform.system() == "Windows":
    from app.core.rippers.video.windows import VideoRipper
elif platform.system() == "Darwin":
    from app.core.rippers.video.macos import VideoRipper