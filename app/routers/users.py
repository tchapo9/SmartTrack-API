from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db
from app.core.security import SecurityService
from app.services.device_service import DeviceService
from app.schemas.device import DeviceResponse

router = APIRouter()


@router.get("/me", response_model=dict)
async def get_profile(current_user = Depends(SecurityService.get_current_active_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role.value,
        "is_active": current_user.is_active,
    }


@router.get("/devices", response_model=list[DeviceResponse])
async def get_devices(
    current_user = Depends(SecurityService.get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    service = DeviceService(db)
    devices = await service.get_user_devices(current_user.id)
    return devices
