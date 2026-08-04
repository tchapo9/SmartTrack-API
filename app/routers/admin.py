from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db
from app.core.security import SecurityService
from app.services.admin_service import AdminService
from app.schemas.user import UserProfileResponse
from app.schemas.device import DeviceResponse
from app.schemas.alert import AlertResponse

router = APIRouter()


@router.get("/users", response_model=list[UserProfileResponse])
async def list_users(
    current_user = Depends(SecurityService.get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    return await service.list_users()


@router.get("/devices", response_model=list[DeviceResponse])
async def list_devices(
    current_user = Depends(SecurityService.get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    return await service.list_devices()


@router.get("/alerts", response_model=list[AlertResponse])
async def list_alerts(
    current_user = Depends(SecurityService.get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    return await service.list_alerts()


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user = Depends(SecurityService.get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    await service.delete_user(user_id)
    return {"message": "User deleted"}
