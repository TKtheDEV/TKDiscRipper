
def rip_other(drive: str, job_id: str):
    from app.backend.job_tracker import JobTracker  # Lazy import to avoid circular import

    """Handles unknown disc types."""
    tracker = JobTracker()
    tracker._update_job(job_id, "⚠️ Unknown disc type detected. No automatic ripper available.", progress=0, status="failed")
    print("unknown disc function called")
    return None