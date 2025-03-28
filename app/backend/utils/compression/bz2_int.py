import subprocess
import shutil

def compress_bz2(input_path: str, output_path: str, on_output: callable = None) -> None:
    if on_output:
        on_output(f"▶️ Compressing {input_path} to {output_path} using bzip2")
    subprocess.run(["bzip2", "-zkf", input_path], check=True)
    shutil.move(f"{input_path}.bz2", output_path)
