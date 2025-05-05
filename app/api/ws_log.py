from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from app.core.job.tracker import job_tracker
import asyncio

ws_router = APIRouter()

@ws_router.websocket("/ws/jobs/{job_id}/log")
async def log_websocket(websocket: WebSocket, job_id: str):
    await websocket.accept()
    try:
        last_sent = 0
        while True:
            await asyncio.sleep(1)
            job = job_tracker.get_job_status(job_id)
            if not job:
                await websocket.send_json({"logs": ["❌ Job not found."]})
                continue

            logs = list(job.get("stdout_log", []))
            new_logs = logs[last_sent:]
            last_sent = len(logs)

            if new_logs:
                await websocket.send_json({"logs": new_logs})

    except WebSocketDisconnect:
        print(f"🔌 WebSocket disconnected: job {job_id}")
