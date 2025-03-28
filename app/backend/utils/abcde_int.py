from backend.utils.logstream import stream_subprocess
from backend.api_helpers import update_job

def run_abcde(
    job_id: str,
    drive_path: str,
    config_path: str,
    output_format: str,
    additional_args: list[str] = None,
) -> bool:
    if additional_args is None:
        additional_args = []

    command = [
        "abcde",
        "-d", drive_path,
        "-B",
        "-N",
        "-o", output_format,
        "-c", config_path,
        *additional_args
    ]

    update_job(job_id, operation="Ripping Audio CD", status="Running abcde...", progress=10)
    update_job(job_id, log=f"$ {' '.join(command)}")

    print(command)
    result = stream_subprocess(command, job_id, update_job)
    print(command)

    if result == 0:
        update_job(job_id, log="✅ abcde finished", progress=90)
        return True
    else:
        update_job(job_id, log="❌ abcde failed", progress=100, status="failed")
        return False
