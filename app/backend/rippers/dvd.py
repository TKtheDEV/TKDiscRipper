import os
import shutil
import re

from backend.rippers.base import BaseRipper
from backend.utils.config_manager import get_config
from backend.utils.handbrake_int import HandBrakeHelper
from backend.utils.makemkv_int import MakeMKVHelper
from backend.api_helpers import get_job, update_job

class DvdRipper(BaseRipper):
    def __init__(self, job_id: str, drive_path: str):
        super().__init__(job_id, drive_path)
        config = get_config()
        self.base_temp = os.path.expanduser(config.get("General", "tempdirectory"))
        self.base_output = os.path.expanduser(config.get("DVD", "outputdirectory"))
        self.handbrake_enabled = config.get("DVD", "usehandbrake", fallback=True)
        self.handbrake_preset = os.path.expanduser(config.get("DVD", "handbrakepreset"))
        self.handbrake_format = config.get("DVD", "handbrakeformat", fallback="mkv")

    def rip(self):
        self.setup_dirs(self.base_temp, self.base_output)

        def log(msg): update_job(self.job_id, log=msg)

        yield f"📁 Temp Dir: {self.temp_dir}"
        yield f"🎬 Disc Label: {self.disc_label}"

        # Start MakeMKV
        yield "🔹 Starting MakeMKV..."
        update_job(self.job_id, operation="Ripping Disc", status="Using MakeMKV to rip disc...", progress=5)
        makemkv_result = MakeMKVHelper.rip_disc(self.drive_path, self.temp_dir, on_output=log)
        update_job(self.job_id, operation="Ripping Disc", status="Finished ripping the disc", progress=50)

        if not makemkv_result:
            update_job(self.job_id, log="❌ MakeMKV failed", progress=100, operation="failed")
            yield "❌ MakeMKV failed"
            return

        # Create output folder with label as subdirectory
        job = get_job(self.job_id) or {}
        label_safe = re.sub(r"[^\w.-]", "_", self.disc_label)[:64]
        output_dir = os.path.join(job.get("output_folder", self.output_dir), label_safe)
        os.makedirs(output_dir, exist_ok=True)

        yield f"📤 Output Dir: {output_dir}"

        if self.handbrake_enabled:
            yield "🎞️ Starting HandBrake..."
            update_job(self.job_id, operation="Transcoding", status="Using HandBrake", progress=55)

            output_files = HandBrakeHelper.transcode(
                self.temp_dir,
                output_dir,
                preset=self.handbrake_preset,
                on_output=log
            )

            if any(output_files):
                update_job(self.job_id, progress=100, status="Task finished", operation="complete")
                yield f"✅ Transcoding complete. Files in: {output_dir}"
            else:
                update_job(self.job_id, progress=100, status="HandBrake failed", operation="failed")
                yield "⚠️ Transcoding failed."
        else:
            yield "📦 Skipping HandBrake. Copying raw MKV files to output..."
            update_job(self.job_id, operation="Copying MKVs", status="Skipping HandBrake", progress=70)

            mkv_files = [f for f in os.listdir(self.temp_dir) if f.endswith(".mkv")]
            for f in mkv_files:
                src = os.path.join(self.temp_dir, f)
                dst = os.path.join(output_dir, f)
                shutil.copy2(src, dst)
                log(f"📄 Copied {f}")

            update_job(self.job_id, progress=100, status="Raw MKVs copied", operation="complete")
            yield f"✅ Copied {len(mkv_files)} MKV file(s) to output."
