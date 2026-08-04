from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db
from app.core.security import SecurityService
from app.services.device_service import DeviceService
from app.schemas.device import DeviceCreate, DeviceUpdate, DeviceResponse

router = APIRouter()


@router.post("/", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    device_data: DeviceCreate,
    current_user = Depends(SecurityService.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    service = DeviceService(db)
    device = await service.register_device(current_user.id, device_data)
    return device


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: int,
    current_user = Depends(SecurityService.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    service = DeviceService(db)
    return await service.get_device(device_id, current_user.id)


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: int,
    device_data: DeviceUpdate,
    current_user = Depends(SecurityService.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    service = DeviceService(db)
    return await service.update_device(device_id, current_user.id, device_data)


@router.post("/{device_id}/activate", response_model=DeviceResponse)
async def activate_device(
    device_id: int,
    current_user = Depends(SecurityService.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    service = DeviceService(db)
    return await service.activate_device(device_id, current_user.id)


@router.post("/{device_id}/deactivate", response_model=DeviceResponse)
async def deactivate_device(
    device_id: int,
    current_user = Depends(SecurityService.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    service = DeviceService(db)
    return await service.deactivate_device(device_id, current_user.id)


@router.post("/{device_id}/lost-mode", response_model=DeviceResponse)
async def set_lost_mode(
    device_id: int,
    enable: bool = True,
    current_user = Depends(SecurityService.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    service = DeviceService(db)
    return await service.set_lost_mode(device_id, current_user.id, enable)


@router.delete("/{device_id}")
async def delete_device(
    device_id: int,
    current_user = Depends(SecurityService.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    service = DeviceService(db)
    await service.delete_device(device_id, current_user.id)
    return {"message": "Device deleted"}
