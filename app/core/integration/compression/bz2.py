import subprocess
import shutil
from typing import Callable

def compress_bz2(input_path: str, output_path: str, on_output: Callable[[str], None]):
    on_output(f"▶️ Compressing {input_path} → {output_path} using bzip2")
    subprocess.run(["bzip2", "-zkf", input_path], check=True)
    shutil.move(f"{input_path}.bz2", output_path)
