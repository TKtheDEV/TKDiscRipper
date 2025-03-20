import os
from backend.utils.makemkv_int import MakeMKVHelper
from backend.utils.handbrake_int import HandBrakeHelper
from backend.utils.config_manager import get_config

class DvdRipper:
    def __init__(self, drive: str, job_id: str, skip_rip: bool = True):
        self.drive = drive
        self.job_id = job_id
        self.makemkv = MakeMKVHelper()
        self.handbrake = HandBrakeHelper()
        
        config = get_config()
        self.temp_dir = os.path.expanduser(config.get("General", "tempdirectory", fallback="~/TKDiscRipper/temp/DVD"))
        self.output_dir = os.path.expanduser(config.get("DVD", "outputdirectory", fallback="~/TKDiscRipper/output/DVD"))
        self.skip_rip = skip_rip
        self.use_handbrake = config.get("DVD", "useHandbrake", fallback="false").lower() == "true"
        self.preset = config.get("DVD", "preset", fallback="Fast 1080p30")

    def rip_dvd(self):
        """Runs the full DVD ripping process and yields logs in real-time."""
        yield f"🚀 Job {self.job_id} started for {self.drive}"

        if not self.skip_rip:
            yield f"📀 Ripping DVD {self.drive} with MakeMKV..."
            mkv_output_paths = self.makemkv.rip_disc(self.drive, self.temp_dir)

            if not mkv_output_paths:
                yield "❌ MakeMKV failed!"
                return

            yield f"✅ MakeMKV completed. MKV files saved to: {self.temp_dir}"

        if self.use_handbrake:
            yield "🎥 Transcoding all MKV files with HandBrake..."
            final_output_paths = self.handbrake.transcode(self.temp_dir, self.output_dir, self.preset)

            if not final_output_paths:
                yield "❌ HandBrake failed!"
                return

            yield f"✅ Transcoding completed. Output files saved to: {self.output_dir}"
        else:
            yield "⏩ Skipping HandBrake transcoding"

if __name__ == "__main__":
    ripper = DvdRipper("/dev/sr1", "qwerty", skip_rip=True)
    for log in ripper.rip_dvd():
        print(log)
