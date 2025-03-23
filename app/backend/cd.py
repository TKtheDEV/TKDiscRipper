import subprocess
import os
from backend.utils.abcde_int import run_abcde
from backend.utils.config_manager import get_config

class CdRipper:
    def __init__(self, drive: str, job_id: str):
        self.drive = drive
        self.job_id = job_id

    def rip_cd(self):
        """Rips an audio CD using abcde."""
        config = get_config()
        yield f"🎵 Starting rip for job {self.job_id} on {self.drive}"
        abcde_preset = os.path.expanduser(config.get("CD", "configpath", fallback="~/TKDiscRipper/config/abcde.conf"))
        output_format = config.get("CD", "outputformat", fallback="flac")
        additional_args = [config.get("CD", "additionaloptions")]

        yield "📀 Running abcde..."
        process = run_abcde(self.drive, abcde_preset, output_format, additional_args)

        if process and process.returncode == 0:
            yield "✅ Audio CD ripped successfully."
        else:
            yield "❌ Audio CD rip failed."
