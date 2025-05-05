from pathlib import Path
from app.core.job_runner import JobRunner
from app.core.config_manager.config_manager import ConfigManager

config = ConfigManager()

async def rip(job):
    makemkv_path = config.get("MAKEMKV.makemkv_path", "makemkvcon")
    default_args = config.get("MAKEMKV.default_args", "--noscan --decrypt --minlength=1")
    output_dir = Path(job.temp_folder)
    output_dir.mkdir(parents=True, exist_ok=True)

    progress_file = output_dir / "makemkv_progress"

    cmd = [
        makemkv_path,
        "--robot",
        "mkv",
        f"dev:{job.drive}",
        "all",
        str(output_dir),
        f"--progress={progress_file}"
    ] + default_args.split()

    job.stdout_log.append(f"Running MakeMKV with: {' '.join(cmd)}")

    runner = JobRunner(cmd, job=job)
    job.runner = runner
    await runner.start()