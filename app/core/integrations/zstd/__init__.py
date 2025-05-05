import platform

if platform.system() == "Linux":
    from app.core.integrations.zstd.linux import compress_zstd
elif platform.system() == "Windows":
    from app.core.integrations.zstd.windows import compress_zstd
elif platform.system() == "Darwin":
    from app.core.integrations.zstd.macos import compress_zstd