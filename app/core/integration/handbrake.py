import os
import re
import subprocess
from typing import Callable, Optional
from app.core.job.context import JobContext

class HandBrake:
    def __init__(self, preset_name: str, preset_file: Optional[str] = None):
        self.preset_name = preset_name
        self.preset_file = preset_file

    def transcode(
        self,
        mkv_files: list[str],
        output_dir: str,
        ctx: JobContext,
    ) -> bool:

        total_tracks = len(mkv_files)
        if total_tracks == 0:
            ctx.log("⚠️ No MKV files found to transcode.")
            return False

        track_weight = 100 / total_tracks

        for idx, mkv_file in enumerate(mkv_files, start=1):
            track_basename = os.path.basename(mkv_file)
            output_path = os.path.join(output_dir, track_basename)
            presetfilecmd = ""
            if self.preset_file:
                presetfilecmd=("--preset-import-file", self.preset_file,)

            ctx.log(f"🎞️ Transcoding file {idx}/{total_tracks}: {track_basename}")
            ctx.log(f"🚀 {mkv_file} → {output_path}")

            command = [
                "flatpak", "run", "--command=HandBrakeCLI", "fr.handbrake.ghb",
                presetfilecmd,
                "-Z", self.preset_name,
                "-i", mkv_file,
                "-o", output_path
            ]

            try:
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                assert process.stdout is not None

                for line in process.stdout:
                    line = line.strip()

                    if "Encoding:" in line and "%" in line:
                        match = re.search(r'(\d+\.\d+)\s+%', line)
                        if match:
                            file_pct = float(match.group(1))
                            progress = int(((idx - 1) + file_pct / 100) * track_weight)
                            ctx.set_progress(progress_step=progress, progress=int(50 + progress * 0.5))

                            eta_match = re.search(r'ETA\s+([\dhms]+)', line)
                            eta = eta_match.group(1) if eta_match else ""
                            ctx.log(f"🎞️ {file_pct:.2f}% {'(ETA ' + eta + ')' if eta else ''}")
                    elif line:
                        ctx.log(line)

                process.wait()
                if process.returncode != 0:
                    ctx.log(f"❌ HandBrake failed on {track_basename}")
                    return False

            except Exception as e:
                ctx.log(f"❌ Error transcoding {mkv_file}: {e}")
                return False

        ctx.log("✅ Transcoding complete.")
        ctx.set_progress(progress=100, progress_step=100)
        return True
