import subprocess
import re
from typing import Optional

class MakeMKVHelper:
    @staticmethod
    def rip_disc(drive_path: str, output_dir: str, on_output: callable = None) -> Optional[str]:
        try:
            command = [
                "makemkvcon", "--robot", "mkv", f"dev:{drive_path}", "all",
                output_dir, "--noscan", "--decrypt", "--minlength=1"
            ]
            process = subprocess.run(command, capture_output=True, text=True, check=True)

            if on_output:
                for line in process.stdout.strip().splitlines():
                    on_output(line)

            match = re.search(r"Saving \d+ titles into directory (file://\S+)", process.stdout)
            if match:
                return match.group(1).replace("file://", "")
            if on_output:
                on_output("❌ MakeMKV did not return a valid output path.")
            return None

        except subprocess.CalledProcessError as e:
            if on_output:
                on_output(f"❌ Error ripping Disc: {e}")
            return None
