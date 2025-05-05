from fastapi import APIRouter
from app.core.systeminfo.systeminfo import get_system_info

router = APIRouter()

@router.get("/api/system-info")
async def system_info():
    return get_system_info()
