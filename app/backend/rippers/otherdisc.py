import os
import threading
import shutil
import logging

from backend.rippers.base import BaseRipper
from backend.utils.config_manager import get_config
from backend.utils.compression.bz2_int import compress_bz2
from backend.utils.compression.zst_int import compress_zst
from backend.utils.logstream import stream_subprocess
from backend.api_helpers import update_job

class OtherDiscRipper(BaseRipper):
    def __init__(self, job_id: str, drive_path: str):
        super().__init__(job_id, drive_path)
        config = get_config()
        self.base_temp = os.path.expanduser(config.get("General", "tempdirectory"))
        self.base_output = os.path.expanduser(config.get("OTHER", "outputdirectory"))
        self.compression = config.get("OTHER", "compression", fallback="bz2").lower()

    def rip(self):
        self.setup_dirs(self.base_temp, self.base_output)
        iso_path = os.path.join(self.temp_dir, f"{self.disc_label}.iso")

        update_job(self.job_id, operation="Ripping Disc", status="Using dd to read disc...", progress=5)
        dd_cmd = ["dd", f"if={self.drive_path}", f"of={iso_path}", "bs=64k", "status=progress"]
        update_job(self.job_id, log=f"$ {' '.join(dd_cmd)}")

        code = stream_subprocess(dd_cmd, self.job_id, update_job)

        if code != 0:
            update_job(self.job_id, log="❌ dd failed", progress=100, status="failed")
            return

        update_job(self.job_id, log="✅ ISO written", progress=60)

        # Compression step
        threading.Thread(target=self._compress_iso, args=(iso_path,), daemon=True).start()

    def _compress_iso(self, iso_path: str):
        ext = self.compression
        final_path = os.path.join(self.output_dir, f"{self.disc_label}.iso.{ext}")

        update_job(self.job_id, operation="Compressing", status=f"Using {ext}", progress=65)

        try:
            if ext == "bz2":
                update_job(self.job_id, log="🔹 Using bzip2")
                compress_bz2(iso_path, final_path)
            elif ext == "zst":
                update_job(self.job_id, log="🔹 Using zstd")
                compress_zst(iso_path, final_path)
            else:
                update_job(self.job_id, log=f"⚠️ Unknown compression '{ext}', skipping")
                shutil.copy2(iso_path, final_path)

            update_job(self.job_id, log="✅ Compression complete", progress=100, status="completed")

        except Exception as e:
            logging.error(f"❌ Compression failed: {e}")
            update_job(self.job_id, log=f"❌ Compression failed: {e}", progress=100, status="failed")
