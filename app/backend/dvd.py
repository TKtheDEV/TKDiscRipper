from backend.rippers.video_disc_ripper import VideoDiscRipper
from backend.utils.config_manager import get_config
from backend.utils.handbrake_int import HandBrakeHelper
from backend.utils.makemkv_int import MakeMKVHelper
import os

class DvdRipper(VideoDiscRipper):
    def __init__(self, job_id: str, drive_path: str):
        super().__init__(job_id, drive_path)
        config = get_config()
        self.base_temp = os.path.expanduser(config.get("General", "tempdirectory"))
        self.base_output = os.path.expanduser(config.get("DVD", "outputdirectory"))
        self.handbrake_preset = config.get("DVD", "handbrakepreset")
        self.handbrake_format = config.get("DVD", "handbrakeformat", fallback="mkv")

    def rip(self):
        self.setup_dirs(self.base_temp, self.base_output, "DVD")
        yield f"📁 Temp Dir: {self.temp_dir}"
        yield f"📤 Output Dir: {self.output_dir}"
        yield f"🎬 Disc Label: {self.disc_label}"

        yield "🔹 Starting MakeMKV..."
        makemkv_result = MakeMKVHelper.rip_disc(self.drive_path, self.temp_dir)

        if not makemkv_result:
            yield "❌ MakeMKV failed."
            return

        if self.handbrake_preset:
            yield "🎞️ Starting HandBrake..."
            output_files = HandBrakeHelper.transcode(
                self.temp_dir,
                self.output_dir,
                preset=self.handbrake_preset
            )
            if any(output_files):
                yield f"✅ Transcoding complete. Files in: {self.output_dir}"
            else:
                yield "⚠️ Transcoding failed or skipped."
        else:
            yield "📦 Skipping HandBrake. Keeping raw MKV files."

if __name__ == "__main__":
    ripper = DvdRipper("/dev/sr1", "qwerty", skip_rip=True)
    for log in ripper.rip_dvd():
        print(log)
