import os
import logging
from utils.makemkv_int import MakeMKVHelper
from utils.handbrake_int import HandBrakeHelper

class BlurayRipper:
    def __init__(self, drive: str, output_dir: str, skip_rip: bool = False):
        self.drive = drive
        self.output_dir = output_dir
        self.makemkv = MakeMKVHelper()
        self.handbrake = HandBrakeHelper()
        self.skip_rip = skip_rip  # Flag to skip ripping
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def rip_disc(self):
        """Runs the full Blu-ray ripping process, or skips ripping if flag is set."""
        logging.info(f"Starting Blu-ray ripping process for drive: {self.drive}")
        
        # Step 1: Skip ripping if the flag is set
        if self.skip_rip:
            logging.info("Skipping Blu-ray ripping. Using files already in the output directory.")
            mkv_output_paths = self.get_mkv_files(self.output_dir)
        else:
            # Rip with MakeMKV
            mkv_output_paths = self.makemkv.rip_disc(self.drive, self.output_dir)
            if not mkv_output_paths:
                logging.error("MakeMKV failed to rip the Blu-ray.")
                return False

            # After ripping, scan the output directory for .mkv files
            logging.info(f"Ripped Blu-ray successfully: {mkv_output_paths}")
            mkv_output_paths = self.get_mkv_files(self.output_dir)

        # Step 2: If no .mkv files are found, log an error
        if not mkv_output_paths:
            logging.error("No MKV files found in the output directory.")
            return False

        logging.info(f"Passing the following files to HandBrake: {mkv_output_paths}")
        
        # Step 3: Transcode with HandBrake
        final_output_paths = self.handbrake.transcode(mkv_output_paths, self.output_dir)
        if not final_output_paths:
            logging.error("HandBrake failed to transcode the Blu-ray.")
            return False
        
        logging.info(f"Transcoding completed: {final_output_paths}")
        return final_output_paths

    def get_mkv_files(self, dir_path: str):
        """Scans the output directory for MKV files."""
        mkv_files = [os.path.join(dir_path, f) for f in os.listdir(dir_path) if f.endswith(".mkv")]
        if not mkv_files:
            logging.error(f"No MKV files found in the directory: {dir_path}")
        return mkv_files

if __name__ == "__main__":
    ripper = BlurayRipper("/dev/sr0", "output", skip_rip=False)
    ripper.rip_disc()
