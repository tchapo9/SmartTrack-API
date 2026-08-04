from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Optional

from app.database.connection import get_db
from app.core.security import SecurityService
from app.services.location_service import LocationService
from app.services.tracking_service import TrackingService
from app.schemas.location import LocationCreate, LocationResponse
from app.schemas.tracking import CurrentPositionResponse

router = APIRouter()


@router.post("/location", response_model=LocationResponse)
async def send_location(
    location_data: LocationCreate,
    db: AsyncSession = Depends(get_db),
):
    service = TrackingService(db)
    return await service.send_location_update(location_data.device_uuid, location_data)


@router.get("/{device_id}/current", response_model=CurrentPositionResponse)
async def current_position(
    device_id: int,
    current_user = Depends(SecurityService.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    service = LocationService(db)
    return await service.get_last_location(device_id, current_user.id)


@router.get("/{device_id}/geojson")
async def get_route_geojson(
    device_id: int,
    current_user = Depends(SecurityService.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    service = LocationService(db)
    return await service.get_route_geojson(device_id, current_user.id)


@router.get("/{device_id}/nearby")
async def nearby_devices(
    latitude: float = Query(...),
    longitude: float = Query(...),
    radius: float = Query(1000.0),
    current_user = Depends(SecurityService.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    service = LocationService(db)
    return await service.find_nearby_devices(latitude, longitude, radius, current_user.id)


@router.get("/{device_id}/statistics")
async def device_statistics(
    device_id: int,
    current_user = Depends(SecurityService.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    service = LocationService(db)
    return await service.get_statistics(device_id, current_user.id)
