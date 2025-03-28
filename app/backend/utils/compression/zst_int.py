import subprocess
import shutil

def compress_zst(input_path: str, output_path: str, on_output: callable = None) -> None:
    if on_output:
        on_output(f"▶️ Compressing {input_path} to {output_path} using zstd")
    subprocess.run(["zstd", "-T0", "-q", input_path], check=True)
    shutil.move(f"{input_path}.zst", output_path)
