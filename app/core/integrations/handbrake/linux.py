from pathlib import Path
from app.core.job_runner import JobRunner
from app.core.config_manager.config_manager import ConfigManager
import subprocess

config = ConfigManager()

async def encode(job, disc_type, input_dir: Path, output_dir: Path):
    section = disc_type if disc_type in config.all() else "DVD"

    preset_name = config.get(f"{section}.handbrakepreset_name", "Very Fast 720p30")
    preset_path = config.get_path(f"{section}.handbrakepreset_path", None)
    output_format = config.get(f"{section}.handbrakeformat", "mkv")
    use_flatpak = config.get("Advanced.HandbrakeFlatpak", True)

    input_files = list(input_dir.glob("*.mkv"))
    if not input_files:
        job.stdout_log.append("No MKV files found to encode.")
        job.status = "Error: No MKV files found for encoding"
        return

    for idx, input_file in enumerate(input_files, 1):
        output_file = output_dir / f"{input_file.stem}_encoded.{output_format}"

        base_cmd = ["HandBrakeCLI"]
        if use_flatpak:
            base_cmd = ["flatpak", "run", "--command=HandBrakeCLI", "fr.handbrake.ghb"]

        cmd = base_cmd + [
            "-i", str(input_file),
            "-o", str(output_file)
        ]

        if preset_path and preset_path.exists():
            cmd += ["--preset-import-file", str(preset_path), "--preset", preset_name]
        else:
            cmd += ["--preset", preset_name]

        job.stdout_log.append(f"Encoding {input_file.name} using section [{section}]...")
        runner = JobRunner(cmd, job=job)
        job.runner = runner
        await runner.start()

def get_available_hw_encoders():
    try:
        result = subprocess.run(
            ["flatpak", "run", "--command=HandBrakeCLI", "fr.handbrake.ghb", "-h"],
            capture_output=True, text=True, check=True
        )
        output = result.stdout.splitlines()

        all_encoders = [line.strip() for line in output if any(v in line for v in ["nvenc_", "qsv_", "vce_"])]

        def extract_codecs(enc_list, prefix):
            return sorted({e.replace(prefix, "") for e in enc_list if e.startswith(prefix)})

        encoders = {
            "nvenc": extract_codecs(all_encoders, "nvenc_"),
            "qsv": extract_codecs(all_encoders, "qsv_"),
            "vce": extract_codecs(all_encoders, "vce_")
        }

        return {
            "vendors": {
                "nvenc": {"label": "NVIDIA NVENC", "available": bool(encoders["nvenc"]), "codecs": encoders["nvenc"]},
                "qsv": {"label": "Intel QSV", "available": bool(encoders["qsv"]), "codecs": encoders["qsv"]},
                "vce": {"label": "AMD VCE", "available": bool(encoders["vce"]), "codecs": encoders["vce"]}
            }
        }

    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        return {
            "vendors": {
                "nvenc": {"label": "NVIDIA NVENC", "available": False, "codecs": []},
                "qsv": {"label": "Intel QSV", "available": False, "codecs": []},
                "vce": {"label": "AMD VCE", "available": False, "codecs": []}
            }
        }