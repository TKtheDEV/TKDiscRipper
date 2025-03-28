from backend.utils.logstream import stream_subprocess

def run_abcde(
    drive_path: str,
    config_path: str,
    output_format: str,
    additional_args: list[str] = None,
    on_output: callable = None
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

    if on_output:
        on_output(f"$ {' '.join(command)}")

    code, _ = stream_subprocess(command, on_output=on_output)
    return code == 0
