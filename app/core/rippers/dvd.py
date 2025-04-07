from app.core.rippers.video import VideoRipper

class DvdRipper(VideoRipper):
    def __init__(self, job_id, drive_path):
        super().__init__(job_id, drive_path, config_section="DVD")
