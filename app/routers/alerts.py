from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database.connection import get_db
from app.core.security import SecurityService
from app.services.alert_service import AlertService
from app.schemas.alert import AlertResponse, AlertStatus

router = APIRouter()


@router.get("/", response_model=list[AlertResponse])
async def list_alerts(
    status: Optional[AlertStatus] = Query(None),
    current_user = Depends(SecurityService.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    service = AlertService(db)
    alerts = await service.list_alerts(current_user.id, status)
    return alerts


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int,
    current_user = Depends(SecurityService.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    service = AlertService(db)
    alert = await service.get_alert(alert_id, current_user.id)
    return alert


@router.put("/{alert_id}/read", response_model=AlertResponse)
async def mark_alert_read(
    alert_id: int,
    current_user = Depends(SecurityService.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    service = AlertService(db)
    alert = await service.mark_alert_as_read(alert_id, current_user.id)
    return alert


@router.put("/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(
    alert_id: int,
    current_user = Depends(SecurityService.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    service = AlertService(db)
    alert = await service.resolve_alert(alert_id, current_user.id)
    return alert
