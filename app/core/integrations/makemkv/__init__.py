import platform

if platform.system() == "Linux":
    from app.core.integrations.makemkv.linux import MakeMKV
elif platform.system() == "Windows":
    from app.core.integrations.makemkv.windows import MakeMKV
elif platform.system() == "Darwin":
    from app.core.integrations.makemkv.macos import MakeMKV