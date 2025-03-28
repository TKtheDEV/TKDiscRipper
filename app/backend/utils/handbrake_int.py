import os
import subprocess

class HandBrakeHelper:
    """Helper class for transcoding videos using HandBrakeCLI."""

    @staticmethod
    def transcode(input_dir: str, output_dir: str, preset: str = "Fast 1080p30") -> list[str]:
        """Transcodes all MKV files in the directory using HandBrakeCLI."""
        output_files = []

        # ✅ Find all MKV files in the directory
        mkv_files = [f for f in os.listdir(input_dir) if f.endswith(".mkv")]
        total = len(mkv_files)
        if not mkv_files:
            print("❌ No MKV files found for transcoding.")
            return []

        print(f"🎥 Found {len(mkv_files)} MKV files for transcoding.")

        for idx, mkv_file in enumerate(mkv_files, start=1):
            input_path = os.path.join(input_dir, mkv_file)
            output_file = os.path.join(output_dir, mkv_file)

            yield f"🎞️ Transcoding file {idx}/{total}: {mkv_file}"

            command = [
                "flatpak", "run", "--command=HandBrakeCLI", "fr.handbrake.ghb",
                "-i", input_path, "-o", output_file, "--preset-import-file", preset
            ]

            try:
                print(f"🚀 Transcoding {input_path} -> {output_file}")
                process = subprocess.run(command, capture_output=True, text=True, check=True)
                print(process.stdout)
                output_files.append(output_file)
            except subprocess.CalledProcessError as e:
                print(f"❌ Error transcoding {input_path}: {e}")
                output_files.append(None)

        return output_files
