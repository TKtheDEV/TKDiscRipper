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

        def log(msg): update_job(self.job_id, log=msg)

        update_job(self.job_id, operation="Ripping Disc", status="Using dd to read disc...", log="▶️ Starting image extraction using dd...", progress=5)
        dd_cmd = ["dd", f"if={self.drive_path}", f"of={iso_path}", "bs=64k", "status=progress"]
        log(f"$ {' '.join(dd_cmd)}")

        code, _ = stream_subprocess(dd_cmd, on_output=log)

        if code != 0:
            update_job(self.job_id, progress=100, operation="failed", status="failed")
            yield f"❌ dd failed"
            return

        update_job(self.job_id, progress=60)
        yield f"✅ ISO created successfully"

        threading.Thread(target=self._compress_iso, args=(iso_path,), daemon=True).start()

    def _compress_iso(self, iso_path: str):
        ext = self.compression
        os.makedirs(self.output_dir, exist_ok=True)
        final_path = os.path.join(self.output_dir, f"{self.disc_label}.iso.{ext}")

        def log(msg): update_job(self.job_id, log=msg)

        update_job(self.job_id, operation="Compressing", status=f"Using {ext} to compress {iso_path}", progress=65)

        try:
            if ext == "bz2":
                log("▶️ Starting compression using bzip2...")
                compress_bz2(iso_path, final_path, on_output=log)
            elif ext == "zst":
                log("▶️ Starting compression using zstd...")
                compress_zst(iso_path, final_path, on_output=log)
            else:
                log(f"⚠️ Unknown format '{ext}', skipping compression...")
                shutil.copy2(iso_path, final_path)

            update_job(self.job_id, log="✅ Compression complete", progress=100, status="completed")

        except Exception as e:
            logging.error(f"❌ Compression failed: {e}")
            update_job(self.job_id, log=f"❌ Compression failed: {e}", progress=100, status="failed")
