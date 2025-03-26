import os
from backend.utils.get_driveinfo import get_drive_info


class VideoDiscRipper:
    """
    Base class for ripping DVD and Blu-ray discs.
    Handles disc label lookup and folder setup for temp and output.
    """

    def __init__(self, job_id: str, drive_path: str):
        self.job_id = job_id
        self.drive_path = os.path.realpath(drive_path)
        self.disc_label = self._get_disc_label()
        self.temp_dir = None
        self.output_dir = None

    def _get_disc_label(self) -> str:
        info = get_drive_info()
        for d in info:
            if os.path.realpath(d["path"]) == self.drive_path:
                return d.get("disc_label", "UNTITLED")
        return "UNTITLED"

    def setup_dirs(self, base_temp: str, base_output: str, subfolder: str):
        self.temp_dir = os.path.join(base_temp, subfolder, self.job_id)
        self.output_dir = os.path.join(base_output, subfolder, self.disc_label)

        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

    def rip(self):
        raise NotImplementedError("Subclasses must implement the rip() method.")
