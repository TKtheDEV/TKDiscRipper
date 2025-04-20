from app.core.job.context import JobContext
from app.core.integration.abcde import run_abcde
from app.core.config import get_config
import os

class AudioRipper:
    def __init__(self, job_id: str, drive_path: str):
        self.job_id = job_id
        self.drive_path = drive_path
        self.ctx = JobContext(job_id)
        self.disc_label = "Disc name not available"
        config = get_config()
        self.output_format = config.get("CD", "outputformat", fallback="flac")
        self.config_path = os.path.expanduser(config.get("CD", "configpath", fallback="~/TKDiscRipper/config/abcde.conf"))
        self.additional_args = config.get("CD", "additionaloptions", fallback="").split()

    def rip(self):
        self.ctx.log("▶️ Starting audio CD rip via abcde...")
        success = run_abcde(
            drive_path=self.drive_path,
            config_path=self.config_path,
            output_format=self.output_format,
            additional_args=self.additional_args,
            on_output=self.ctx.log
        )

        if success:
            yield "✅ Audio CD ripped successfully."
        else:
            yield "❌ Audio CD rip failed."
