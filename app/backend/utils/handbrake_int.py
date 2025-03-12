import os
import subprocess

class HandBrakeHelper:
    """Helper class for transcoding videos using HandBrakeCLI."""

    @staticmethod
    def transcode(input_paths: list[str], output_dir: str, preset: str = "Fast 1080p30") -> list[str]:
        """Transcodes the MKV files using HandBrakeCLI."""
        output_files = []
        
        for input_path in input_paths:
            output_file = os.path.join(output_dir, os.path.basename(input_path).replace(".mkv", ".mp4"))

            command = ["flatpak", "run", "--command=HandBrakeCLI", "fr.handbrake.ghb",
                    "-i", input_path, "-o", output_file, "--preset", preset]

            try:
                process = subprocess.run(command, capture_output=True, text=True, check=True)
                print(process.stdout)
                output_files.append(output_file)
            except subprocess.CalledProcessError as e:
                print(f"Error during transcoding {input_path}: {e}")
                output_files.append(None)  # Mark as failed
        
        return output_files
