from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db
from app.core.security import SecurityService
from app.services.geofence_service import GeofenceService
from app.schemas.geofence import GeofenceCreate, GeofenceResponse

router = APIRouter()


@router.post("/", response_model=GeofenceResponse, status_code=status.HTTP_201_CREATED)
async def create_geofence(
    geofence_data: GeofenceCreate,
    current_user = Depends(SecurityService.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    service = GeofenceService(db)
    return await service.create_geofence(current_user.id, geofence_data)


@router.get("/", response_model=list[GeofenceResponse])
async def list_geofences(
    current_user = Depends(SecurityService.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    service = GeofenceService(db)
    return await service.list_geofences(current_user.id)


@router.get("/{geofence_id}", response_model=GeofenceResponse)
async def get_geofence(
    geofence_id: int,
    current_user = Depends(SecurityService.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    service = GeofenceService(db)
    return await service.get_geofence(geofence_id, current_user.id)


@router.put("/{geofence_id}", response_model=GeofenceResponse)
async def update_geofence(
    geofence_id: int,
    geofence_data: GeofenceCreate,
    current_user = Depends(SecurityService.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    service = GeofenceService(db)
    return await service.update_geofence(geofence_id, current_user.id, geofence_data)


@router.delete("/{geofence_id}")
async def delete_geofence(
    geofence_id: int,
    current_user = Depends(SecurityService.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    service = GeofenceService(db)
    await service.delete_geofence(geofence_id, current_user.id)
    return {"message": "Geofence deleted"}
