import subprocess
import shutil

def compress_zst(input_path: str, output_path: str) -> None:
    """
    Compresses the given ISO file using zstd.
    """
    subprocess.run(["zstd", "-T0", "-q", input_path], check=True)
    shutil.move(f"{input_path}.zst", output_path)
