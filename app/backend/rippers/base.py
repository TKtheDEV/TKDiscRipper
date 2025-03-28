import os
import re
from backend.utils.get_driveinfo import get_drive_info
from backend.api_helpers import update_job

class BaseRipper:
    """
    Abstract base for all disc rippers (CD, DVD, Blu-ray).
    Handles disc label lookup and temp/output folder creation.
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

    def setup_dirs(self, base_temp: str, base_output: str):
        """
        Sets self.temp_dir and self.output_dir (uncreated).
        """
        # temp dir = temp/<job_id>/
        self.temp_dir = os.path.join(base_temp, self.job_id)
        os.makedirs(self.temp_dir, exist_ok=True)

        # output dir = output/<disc_label> — NOT created yet
        safe_label = re.sub(r"[^\w.-]", "_", self.disc_label)[:64]
        self.output_dir = os.path.join(os.path.expanduser(base_output), safe_label)

        update_job(self.job_id, temp_folder=self.temp_dir, output_folder=self.output_dir)

    def rip(self):
        raise NotImplementedError("Subclasses must implement rip()")