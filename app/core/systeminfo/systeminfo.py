import platform
import importlib
from typing import Dict

def get_system_info() -> Dict:
    system = platform.system().lower()
    if system == "linux":
        mod = importlib.import_module("app.core.systeminfo.linux")
    elif system == "windows":
        mod = importlib.import_module("app.core.systeminfo.windows")
    elif system == "darwin":
        mod = importlib.import_module("app.core.systeminfo.macos")
    else:
        raise NotImplementedError(f"Unsupported system: {system}")
    return mod.get_system_info()

if __name__ == "__main__":
    import json
    import sys
    try:
        info = get_system_info()
        print(json.dumps(info, indent=2))
    except Exception as e:
        print(f"System info fetch failed: {e}", file=sys.stderr)
        sys.exit(1)