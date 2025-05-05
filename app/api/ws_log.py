from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.job_tracker import JobTracker
import asyncio

router = APIRouter()
tracker = JobTracker()

@router.websocket("/jobs/{job_id}/log")
async def job_log_socket(websocket: WebSocket, job_id: str):
    await websocket.accept()

    job = tracker.get_job(job_id)
    if not job:
        await websocket.send_text("Job not found.")
        await websocket.close()
        return

    last_index = 0

    try:
        while True:
            await asyncio.sleep(0.5)
            log_lines = list(job.stdout_log)
            if len(log_lines) > last_index:
                for line in log_lines[last_index:]:
                    await websocket.send_text(line)
                last_index = len(log_lines)
    except WebSocketDisconnect:
        pass