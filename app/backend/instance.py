from backend.job_tracker import JobTracker
from backend.drive_tracker import get_drive_tracker

tracker = JobTracker()
tracker.drive_tracker = get_drive_tracker()  # manual injection
