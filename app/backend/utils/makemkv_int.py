import subprocess
import re
from typing import List, Optional

class MakeMKVHelper:
    """Helper class for handling Blu-ray ripping using MakeMKV."""
    @staticmethod
    def rip_disc(drive_path: str, output_dir: str) -> Optional[str]:
        """Rips a Blu-ray disc from the specified drive to MKV format."""

        try:
            command = ["makemkvcon", "--robot", "mkv", f"dev:{drive_path}", "all", output_dir, "--noscan", "--decrypt", "--minlength=1"]
            process = subprocess.run(command, capture_output=True, text=True, check=True)
            print(process.stdout)

            # Extract the output path
            match = re.search(r"Saving \d+ titles into directory (file://\S+)", process.stdout)
            if match:
                mkv_output_path = match.group(1).replace("file://", "")  # Remove file:// prefix
                return mkv_output_path

            print("❌ MakeMKV did not return a valid output path.")
            return None
        except subprocess.CalledProcessError as e:
            print(f"❌ Error ripping Disc: {e}")
            return None

if __name__ == "__main__":
    output_dir = "/home/arm/Videos"
    drive_path = "/dev/sr1"
    
    print(f"📀 Starting rip for {drive_path}...")
    result = MakeMKVHelper.rip_disc(drive_path, output_dir)
    if result:
        print(f"✅ Ripping completed: {result}")
    else:
        print("❌ Ripping failed.")