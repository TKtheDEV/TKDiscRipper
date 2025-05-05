import platform

if platform.system() == "Linux":
    from app.core.systeminfo.linux import LinuxSystemInfo as SystemInfo
elif platform.system() == "Windows":
    from app.core.systeminfo.windows import WindowsSystemInfo as SystemInfo
elif platform.system() == "Darwin":
    from app.core.systeminfo.macos import MacosSystemInfo as SystemInfo
