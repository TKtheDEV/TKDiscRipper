import os
import subprocess

class HandBrakeHelper:
    """Helper class for transcoding videos using HandBrakeCLI."""

    @staticmethod
    def transcode(input_dir: str, output_dir: str, preset: str = "Fast 1080p30", on_output: callable = None) -> list[str]:
        output_files = []
        mkv_files = [f for f in os.listdir(input_dir) if f.endswith(".mkv")]
        total = len(mkv_files)

        if not mkv_files:
            if on_output:
                on_output("❌ No MKV files found for transcoding.")
            return []

        if on_output:
            on_output(f"🎥 Found {len(mkv_files)} MKV files for transcoding.")

        for idx, mkv_file in enumerate(mkv_files, start=1):
            input_path = os.path.join(input_dir, mkv_file)
            output_file = os.path.join(output_dir, mkv_file)

            if on_output:
                on_output(f"🎞️ Transcoding file {idx}/{total}: {mkv_file}")
                on_output(f"🚀 Transcoding {input_path} -> {output_file}")

            command = [
                "flatpak", "run", "--command=HandBrakeCLI", "fr.handbrake.ghb",
                "-i", input_path, "-o", output_file, "--preset-import-file", preset
            ]

            try:
                process = subprocess.run(command, capture_output=True, text=True, check=True)
                if on_output:
                    on_output(process.stdout.strip())
                output_files.append(output_file)
            except subprocess.CalledProcessError as e:
                if on_output:
                    on_output(f"❌ Error transcoding {input_path}: {e}")
                output_files.append(None)

        return output_files
