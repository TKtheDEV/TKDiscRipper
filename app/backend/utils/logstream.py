import subprocess

def stream_subprocess(
    command: list[str],
    job_id: str,
    update_func,
    capture_output: bool = False
) -> tuple[int, str | None]:
    """
    Runs a command, streams its output to the job log, and optionally captures it.

    Returns:
        (exit_code, full_output or None)
    """
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
            update_func(job_id, log=line)
            if capture_output:
                captured.append(line)

    process.stdout.close()
    returncode = process.wait()

    return (returncode, "\n".join(captured) if capture_output else None)
