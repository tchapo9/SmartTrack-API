from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db
from app.core.security import SecurityService
from app.services.location_service import LocationService
from app.schemas.location import LocationResponse

router = APIRouter()


@router.get("/{device_id}/last", response_model=LocationResponse)
async def get_last_location(
    device_id: int,
    current_user = Depends(SecurityService.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    service = LocationService(db)
    location = await service.get_last_location(device_id, current_user.id)
    return location


@router.get("/{device_id}/history", response_model=list[LocationResponse])
async def get_location_history(
    device_id: int,
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    current_user = Depends(SecurityService.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    service = LocationService(db)
    return await service.get_location_history(device_id, current_user.id, start_date, end_date)
