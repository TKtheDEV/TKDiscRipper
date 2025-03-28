import subprocess
import shutil

def compress_bz2(input_path: str, output_path: str) -> None:
    """
    Compresses the given ISO file using bzip2.
    """
    subprocess.run(["bzip2", "-zkf", input_path], check=True)  # -z: compress, -k: keep original
    shutil.move(f"{input_path}.bz2", output_path)
