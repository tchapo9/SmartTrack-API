from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db
from app.core.security import SecurityService
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/overview")
async def dashboard_overview(
    current_user = Depends(SecurityService.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    service = DashboardService(db)
    return await service.get_overview(current_user.id)


@router.get("/device/{device_id}")
async def device_summary(
    device_id: int,
    current_user = Depends(SecurityService.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    service = DashboardService(db)
    return await service.get_device_summary(device_id, current_user.id)
