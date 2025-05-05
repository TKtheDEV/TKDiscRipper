import platform

if platform.system() == "Linux":
    from app.core.integrations.handbrake.linux import HandBrake
elif platform.system() == "Windows":
    from app.core.integrations.handbrake.windows import HandBrake
elif platform.system() == "Darwin":
    from app.core.integrations.handbrake.macos import HandBrake