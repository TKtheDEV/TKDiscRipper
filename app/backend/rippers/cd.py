import os
from backend.rippers.base import BaseRipper
from backend.utils.abcde_int import run_abcde
from backend.utils.config_manager import get_config
from backend.api_helpers import update_job

class CdRipper(BaseRipper):
    def __init__(self, job_id: str, drive_path: str):
        super().__init__(job_id, drive_path)
        config = get_config()
        self.output_format = config.get("CD", "outputformat", fallback="flac")
        self.config_path = os.path.expanduser(config.get("CD", "configpath", fallback="~/TKDiscRipper/config/abcde.conf"))
        self.additional_args = config.get("CD", "additionaloptions", fallback="").split()

    def rip(self):
        def log(msg): update_job(self.job_id, log=msg)

        update_job(self.job_id, operation="Ripping", log="▶️ Starting disc backup using abcde...", status="Running abcde to back up audio cd...", progress=10)

        success = run_abcde(
            drive_path=self.drive_path,
            config_path=self.config_path,
            output_format=self.output_format,
            additional_args=self.additional_args,
            on_output=log
        )

        if success:
            yield "✅ Audio CD ripped successfully."
        else:
            yield "❌ Audio CD rip failed."
