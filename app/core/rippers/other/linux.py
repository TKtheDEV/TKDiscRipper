import os
import shutil
import threading
from app.core.config import get_config
from app.core.job.context import JobContext
from app.core.integrations.bz2 import compress_bz2
from app.core.integrations.zstd import compress_zstd
from app.core.logstream import stream_subprocess
from app.core.driveinfo.linux import LinuxDriveInfo

class IsoRipper:
    def __init__(self, job_id: str, drive_path: str):
        self.job_id = job_id
        self.drive_path = drive_path
        self.ctx = JobContext(job_id)

        self.disc_label = self._get_disc_label()  

        config = get_config()
        self.base_temp = os.path.expanduser(config.get("General", "tempdirectory"))
        self.base_output = os.path.expanduser(config.get("OTHER", "outputdirectory"))
        self.compression = config.get("OTHER", "compression", fallback="bz2").lower()

        self.temp_dir = os.path.join(self.base_temp, job_id) 
        self.output_dir = self.base_output                   

        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

    def _get_disc_label(self) -> str:
        info = LinuxDriveInfo().get_drive_info()
        for d in info:
            if os.path.realpath(d["path"]) == os.path.realpath(self.drive_path):
                return d.get("disc_label", "UNTITLED")
        return "UNTITLED"

    def rip(self):
        iso_path = os.path.join(self.temp_dir, f"{self.job_id}.iso")
        self.ctx.set_progress(operation="Ripping Disc", status="Reading via dd", progress=5)

        dd_cmd = ["dd", f"if={self.drive_path}", f"of={iso_path}", "bs=64k", "status=progress"]
        self.ctx.log(f"$ {' '.join(dd_cmd)}")
        code, _ = stream_subprocess(dd_cmd, on_output=self.ctx.log)

        if code != 0:
            self.ctx.set_progress(progress=100, operation="failed", status="dd failed")
            yield "❌ dd failed"
            return

        self.ctx.set_progress(progress=60)
        yield "✅ ISO created successfully"

        threading.Thread(target=self._compress_iso, args=(iso_path,), daemon=True).start()

    def _compress_iso(self, iso_path: str):
        final_path = os.path.join(self.output_dir, f"{self.job_id}.iso.{self.compression}")
        self.ctx.set_progress(operation="Compressing", status=f"Compressing {iso_path}", progress=65)

        try:
            if self.compression == "bz2":
                compress_bz2(iso_path, final_path, self.ctx.log)
            elif self.compression == "zstd":
                compress_zstd(iso_path, final_path, self.ctx.log)
            else:
                shutil.copy2(iso_path, final_path)

            self.ctx.log("✅ Compression complete")
            self.ctx.set_progress(progress=100, status="completed")

        except Exception as e:
            self.ctx.log(f"❌ Compression failed: {e}")
            self.ctx.set_progress(progress=100, status="failed")
