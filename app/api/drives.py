from fastapi import APIRouter, Request
from pydantic import BaseModel
from app.core.drive_tracker import drive_tracker as tracker
from app.core.drivemanager import linux as drivemanager

router = APIRouter()

@router.get("/api/drives")
def list_drives(): 
    drives = tracker.get_all()
    return [drive.to_dict() for drive in drives]

class EjectRequest(BaseModel):
    drive: str

@router.post("/api/drives/eject")
def eject_drive(req: EjectRequest):
    success = drivemanager.eject_drive(req.drive)
    return { "success": success }