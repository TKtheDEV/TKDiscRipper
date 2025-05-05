import platform

if platform.system() == "Linux":
    from app.core.integrations.bz2.linux import compress_bz2
elif platform.system() == "Windows":
    from app.core.integrations.bz2.windows import compress_bz2
elif platform.system() == "Darwin":
    from app.core.integrations.bz2.macos import compress_bz2