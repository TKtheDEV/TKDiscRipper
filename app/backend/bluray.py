import os
import logging
import subprocess
from backend.utils.makemkv_int import MakeMKVHelper
from backend.utils.handbrake_int import HandBrakeHelper
from backend.job_tracker import JobTracker
from backend.utils.config_manager import get_config

class BlurayRipper:
    def __init__(self, drive: str, job_id: str):
        self.drive = drive
        self.job_id = job_id
        self.makemkv = MakeMKVHelper()
        self.handbrake = HandBrakeHelper()
        self.tracker = JobTracker()

        # Get output directory from config
        config = get_config()
        self.output_dir = config.get("paths", "output_dir", fallback="output")

    def rip_bluray(self):
        """Runs the full Blu-ray ripping process with status updates."""

        # Step 1: Mark job as "starting"
        self.tracker._update_job(self.job_id, "🚀 Job started: Preparing for ripping...", progress=0, status="starting")

        # Step 2: Rip with MakeMKV
        self.tracker._update_job(self.job_id, "📀 Ripping Blu-ray with MakeMKV...", progress=5, status="ripping")
        mkv_output_paths = self.makemkv.rip_disc(self.drive, self.output_dir)
        if not mkv_output_paths:
            self.tracker._update_job(self.job_id, "❌ MakeMKV failed.", progress=5, status="failed")
            return False

        self.tracker._update_job(self.job_id, f"✅ MakeMKV completed: {mkv_output_paths}", progress=50)

        # Step 3: Eject the disc
        self.eject_disc()

        # Step 4: Transcode with HandBrake
        self.tracker._update_job(self.job_id, "🎥 Transcoding video with HandBrake...", progress=55, status="transcoding")
        final_output_paths = self.handbrake.transcode(mkv_output_paths, self.output_dir)
        if not final_output_paths:
            self.tracker._update_job(self.job_id, "❌ HandBrake failed.", progress=55, status="failed")
            return False

        self.tracker._update_job(self.job_id, f"✅ Transcoding completed: {final_output_paths}", progress=100, status="done")
        return final_output_paths

    def eject_disc(self):
        """Ejects the disc drive after ripping is complete."""
        try:
            self.tracker._update_job(self.job_id, f"🔄 Ejecting disc from {self.drive}...")
            subprocess.run(["eject", self.drive], check=True)
            self.tracker._update_job(self.job_id, "💿 Disc ejected successfully.")
        except subprocess.CalledProcessError as e:
            self.tracker._update_job(self.job_id, f"⚠️ Warning: Could not eject disc ({e})")

    def get_mkv_files(self, dir_path: str):
        """Scans the output directory for MKV files."""
        mkv_files = [os.path.join(dir_path, f) for f in os.listdir(dir_path) if f.endswith(".mkv")]
        if not mkv_files:
            logging.error(f"No MKV files found in the directory: {dir_path}")
        return mkv_files

if __name__ == "__main__":
    ripper = BlurayRipper("/dev/sr0", "output", skip_rip=False)
    ripper.rip_bluray()
