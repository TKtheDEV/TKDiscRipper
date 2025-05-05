import platform
import importlib
import shutil
from pathlib import Path
from app.core.config_manager.config_manager import ConfigManager

config = ConfigManager()

def import_platform_module(base_path: str):
    system = platform.system().lower()
    if system == "linux":
        return importlib.import_module(f"{base_path}.linux")
    elif system == "windows":
        return importlib.import_module(f"{base_path}.windows")
    elif system == "darwin":
        return importlib.import_module(f"{base_path}.macos")
    else:
        raise NotImplementedError(f"Unsupported platform: {system}")

async def start(job):
    job.step_description = "Ripping with MakeMKV"

    # Import platform-specific MakeMKV module and rip
    makemkv = import_platform_module("app.core.integrations.makemkv")
    await makemkv.rip(job)

    job.step += 1
    job.step_progress = 100
    job.progress = 50

    if config.get("DVD.usehandbrake", True):
        job.step_description = "Encoding with HandBrake"

        # Import platform-specific HandBrake module
        handbrake = import_platform_module("app.core.integrations.handbrake")
        await handbrake.encode(
            job,
            disc_type=job.disc_type,
            input_dir=Path(job.output_folder),
            output_dir=Path(job.output_folder)
        )

        job.step_progress = 100
        job.progress = 100
        job.status = "Finished encoding"

    else:
        job.step_description = "Copying to output folder (no HandBrake)"
        for file in Path(job.temp_folder).glob("*.mkv"):
            dest = Path(job.output_folder) / file.name
            shutil.copy(file, dest)
            job.stdout_log.append(f"Copied {file.name} to output directory.")

        job.step_progress = 100
        job.progress = 100
        job.status = "Finished ripping (no HandBrake)"
