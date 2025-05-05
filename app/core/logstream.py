import subprocess
from typing import Callable

def stream_subprocess(
    command: list[str],
    on_output: Callable[[str], None] = None,
    capture_output: bool = False
) -> tuple[int, str | None]:
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    captured = [] if capture_output else None

    for line in iter(process.stdout.readline, ''):
        line = line.strip()
        if line:
            if on_output:
                on_output(line)
            if capture_output:
                captured.append(line)

    process.stdout.close()
    returncode = process.wait()
    return (returncode, "\n".join(captured) if capture_output else None)
