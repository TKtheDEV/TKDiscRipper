import subprocess
from backend.utils.abcde_int import run_abcde
from backend.utils.config_manager import get_config

class CdRipper:
    def __init__(self, drive: str, job_id: str):
        self.drive = drive
        self.job_id = job_id
        config = get_config()
        self.output_dir = config.get("paths", "output_dir", fallback="output")

    def rip_cd(self):
        """Rips an audio CD using abcde."""
        yield f"🎵 Starting rip for job {self.job_id} on {self.drive}"
        config_file = "/home/arm/TKDiscRipper/config/abcde.conf"
        output_format = "flac"
        additional_args = ["-B"]

        yield "📀 Running abcde..."
        process = run_abcde(self.drive, config_file, output_format, additional_args)

        if process and process.returncode == 0:
            yield "✅ Audio CD ripped successfully."
        else:
            yield "❌ Audio CD rip failed."
