import subprocess
import logging

# Logging Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def run_abcde(drive_path, config_file, output_format, additional_args=None):
    """
    Runs abcde to rip an audio CD.

    Args:
        drive_path (str): Path to the CD drive (e.g., /dev/sr0).
        config_file (str): Path to the abcde configuration file.
        output_format (str): Desired output format (e.g., flac, mp3).
        additional_args (list): Optional additional arguments for abcde.

    Returns:
        bool: True if abcde completes successfully, False otherwise.
    """
    try:
        logging.info(f"Starting abcde for drive: {drive_path}")
        logging.info(f"Config file: {config_file}, Output format: {output_format}")
        
        if additional_args:
            logging.info(f"Additional Args: {additional_args}")
        else:
            logging.info("No additional arguments provided.")

        # Ensure additional_args is a list (or empty if None)
        additional_args = additional_args or []

        # Construct the abcde command
        command = [
            "abcde",
            "-d", drive_path,
            "-N",
            "-o", output_format,
            "-c", config_file,
            "-x"
        ] + additional_args  # Append additional arguments if provided

        logging.info(f"Constructed Command: {' '.join(command)}")

        # Run abcde and capture its real-time output
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        # Stream output in real-time
        for line in process.stdout:
            logging.info(line.strip())  # Log the output in real-time

        # Wait for the process to complete
        process.wait()

        if process.returncode == 0:
            logging.info("abcde completed successfully.")
            return True
        else:
            logging.error(f"abcde failed with exit code {process.returncode}.")
            return False
    except Exception as e:
        logging.error(f"Error running abcde: {e}")
        return False


if __name__ == "__main__":
    drive = "/dev/sr0"
    config = "/home/tk22/Github/GOATripper/abcdebase.conf"
    output_format = "flac"
    additional_arguments = ["-B"]
    success = run_abcde(drive, config, output_format, additional_arguments)
    if success:
        print("Ripping completed successfully!")
    else:
        print("Ripping failed.")