import platform

if platform.system() == "Linux":
    from app.core.rippers.other.linux import IsoRipper
elif platform.system() == "Windows":
    from app.core.rippers.other.windows import IsoRipper
elif platform.system() == "Darwin":
    from app.core.rippers.other.macos import IsoRipper
