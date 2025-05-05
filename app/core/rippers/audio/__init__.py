import platform

if platform.system() == "Linux":
    from app.core.rippers.audio.linux import AudioRipper
elif platform.system() == "Windows":
    from app.core.rippers.audio.windows import AudioRipper
elif platform.system() == "Darwin":
    from app.core.rippers.audio.macos import AudioRipper