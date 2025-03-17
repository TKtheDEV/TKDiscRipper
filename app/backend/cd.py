from .utils.abcde_int import run_abcde

if __name__ == "__main__":
    drive = "/dev/sr0"
    config = "/home/tk22/TKDiscRipper/config/abcde.conf"
    output_format = "flac"
    additional_arguments = ["-B"]
    success = run_abcde(drive, config, output_format, additional_arguments)
    if success:
        print("Ripping completed successfully!")
    else:
        print("Ripping failed.")