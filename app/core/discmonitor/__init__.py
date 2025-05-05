import platform
import importlib

def monitor_disc_events():
    system = platform.system().lower()
    if system == "linux":
        mod = importlib.import_module("app.core.discmonitor.linux")
    elif system == "windows":
        mod = importlib.import_module("app.core.discmonitor.windows")
    elif system == "darwin":
        mod = importlib.import_module("app.core.discmonitor.macos")
    else:
        raise NotImplementedError(f"Unsupported OS: {system}")
    return mod.monitor_disc_events()