import os
import threading
from typing import Optional
from app.core.logstream import stream_subprocess
from app.core.job.context import JobContext

class MakeMKV:
    def rip(self, drive_path: str, temp_dir: str, ctx: JobContext) -> Optional[str]:
        progress_path = os.path.join(temp_dir, f"{ctx.job_id}_progress.txt")

        command = [
            "makemkvcon", "--robot", "mkv", f"dev:{drive_path}", "all",
            temp_dir, "--noscan", "--decrypt", "--minlength=1",
            f"--progress={progress_path}"
        ]

        ctx.log(f"$ {' '.join(command)}")

        threading.Thread(
            target=self._watch_progress_file,
            args=(progress_path, ctx),
            daemon=True
        ).start()

        code, _ = stream_subprocess(command, on_output=ctx.log)

        if code != 0:
            ctx.log(f"❌ MakeMKV exited with code {code}")
            return None

        if os.path.exists(progress_path):
            os.remove(progress_path)

        ctx.set_progress(progress_step=100, progress=50)
        return temp_dir

    def _watch_progress_file(self, path: str, ctx: JobContext):
        last_pos = 0
        while True:
            try:
                with open(path, "r") as f:
                    f.seek(last_pos)
                    for line in f:
                        line = line.strip()
                        if line.startswith("PRGV:"):
                            _, disc_pct, max_val = line.split(":")[1].split(",")
                            max_val = int(max_val)
                            step_pct = int((int(disc_pct) / max_val) * 100) if max_val else 0
                            ctx.set_progress(current_phase="makemkv", progress_step=step_pct, progress=int(step_pct * 0.5))
                        elif line.startswith("PRGC:"):
                            _, _, status = line.split(",", 2)
                            ctx.log(f"📘 {status.strip('\"')}")
                    last_pos = f.tell()
            except Exception:
                pass
            import time; time.sleep(1)
