import subprocess

def stream_subprocess(command: list[str], job_id: str, update_func):
    """
    Runs command and pushes stdout lines into job log in real-time.
    """
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    for line in process.stdout:
        update_func(job_id, log=line.strip())

    process.wait()
    return process.returncode
