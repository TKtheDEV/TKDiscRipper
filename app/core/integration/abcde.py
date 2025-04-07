import subprocess
from typing import Optional, Callable

def run_abcde(
    drive_path: str,
    config_path: str,
    output_format: str,
    additional_args: list[str],
    on_output: Optional[Callable[[str], None]] = None
) -> bool:
    command = [
        "abcde",
        "-d", drive_path,
        "-o", output_format,
        "-c", config_path,
        *additional_args
    ]

    if on_output:
        on_output(f"$ {' '.join(command)}")

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    assert process.stdout is not None

    for line in process.stdout:
        line = line.strip()
        if line and on_output:
            on_output(line)

    process.wait()
    return process.returncode == 0
