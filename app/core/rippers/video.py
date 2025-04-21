import os
import re
import shutil
from app.core.config import get_config
from app.core.job.context import JobContext
from app.core.integration.makemkv import MakeMKV
from app.core.integration.handbrake import HandBrake
from app.core.os.linux_driveinfo import LinuxDriveInfo

class VideoRipper:
    def __init__(self, job_id: str, drive_path: str, config_section: str):
        self.job_id = job_id
        self.drive_path = os.path.realpath(drive_path)
        self.ctx = JobContext(job_id)
        self.config_section = config_section.upper()
        self.disc_label = self._get_disc_label()

        config = get_config()
        self.base_temp = os.path.expanduser(config.get("General", "tempdirectory"))
        self.base_output = os.path.expanduser(config.get(self.config_section, "outputdirectory"))
        self.handbrake_enabled = config.get(self.config_section, "usehandbrake", fallback="true").lower() == "true"
        self.handbrake_preset_name = os.path.expanduser(config.get(self.config_section, "handbrakepreset_name"))
        self.handbrake_preset_path = os.path.expanduser(config.get(self.config_section, "handbrakepreset_path"))
        self.handbrake_format = config.get(self.config_section, "handbrakeformat", fallback="mkv")

        self.temp_dir = None
        self.output_dir = None

    def _get_disc_label(self) -> str:
        info = LinuxDriveInfo().get_drive_info()
        for d in info:
            if os.path.realpath(d["path"]) == self.drive_path:
                return d.get("disc_label", "UNTITLED")
        return "UNTITLED"

    def setup_dirs(self):
        self.temp_dir = os.path.join(self.base_temp, self.job_id)
        os.makedirs(self.temp_dir, exist_ok=True)

        safe_label = re.sub(r"[^\w.-]", "_", self.disc_label)[:64]
        self.output_dir = os.path.join(os.path.expanduser(self.base_output), safe_label)
        os.makedirs(self.output_dir, exist_ok=True)

        self.ctx.set_progress(temp_folder=self.temp_dir, output_folder=self.output_dir)

    def rip(self):
        self.setup_dirs()
        yield f"📁 Temp Dir: {self.temp_dir}"
        yield f"🎬 Disc Label: {self.disc_label}"

        yield "🔹 Starting MakeMKV..."
        self.ctx.set_progress(operation="Ripping Disc", status="Using MakeMKV to rip...", progress=5)
        makemkv = MakeMKV()
        if not makemkv.rip(self.drive_path, self.temp_dir, self.ctx):
            yield "❌ MakeMKV failed"
            self.ctx.set_progress(status="MakeMKV failed", progress=100, operation="failed")
            return

        yield f"📤 Output Dir: {self.output_dir}"

        mkvs = [os.path.join(self.temp_dir, f) for f in os.listdir(self.temp_dir) if f.endswith(".mkv")]

        if self.handbrake_enabled:
            yield "🎞️ Starting HandBrake..."
            self.ctx.set_progress(operation="Transcoding", status="Using HandBrake", progress=55)
            hb = HandBrake(self.handbrake_preset_name, self.handbrake_preset_path)
            if hb.transcode(mkvs, self.output_dir, self.ctx):
                yield f"✅ Transcoding complete. Files in: {self.output_dir}"
                self.ctx.set_progress(operation="complete", status="Done", progress=100)
            else:
                yield "⚠️ HandBrake failed"
                self.ctx.set_progress(operation="failed", status="HandBrake failed", progress=100)
        else:
            yield "📦 Skipping HandBrake. Copying raw MKVs..."
            for f in mkvs:
                shutil.copy2(f, os.path.join(self.output_dir, os.path.basename(f)))
                self.ctx.log(f"📄 Copied {f}")
            self.ctx.set_progress(operation="complete", status="Raw MKVs copied", progress=100)
            yield f"✅ Copied {len(mkvs)} MKV files to output."
