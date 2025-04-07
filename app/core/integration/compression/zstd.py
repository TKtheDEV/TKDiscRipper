import subprocess
import shutil
from typing import Callable

def compress_zst(input_path: str, output_path: str, on_output: Callable[[str], None]):
    on_output(f"▶️ Compressing {input_path} → {output_path} using zstd")
    subprocess.run(["zstd", "-T0", "-q", input_path], check=True)
    shutil.move(f"{input_path}.zst", output_path)
