from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Any, List
from datetime import datetime

from app.models.alert import Alert, AlertType, AlertStatus
from app.models.device import Device
from app.core.exceptions import NotFoundError


class AlertService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_alerts(self, user_id: int, status: AlertStatus | None = None) -> List[Alert]:
        query = select(Alert).where(Alert.user_id == user_id)
        if status is not None:
            query = query.where(Alert.status == status)
        result = await self.db.execute(query.order_by(Alert.created_at.desc()))
        return result.scalars().all()

    async def get_alert(self, alert_id: int, user_id: int) -> Alert:
        result = await self.db.execute(
            select(Alert).where(Alert.id == alert_id, Alert.user_id == user_id)
        )
        alert = result.scalar_one_or_none()
        if not alert:
            raise NotFoundError("Alert not found")
        return alert

    async def mark_alert_as_read(self, alert_id: int, user_id: int) -> Alert:
        alert = await self.get_alert(alert_id, user_id)
        alert.status = AlertStatus.READ
        alert.read_at = datetime.utcnow()
        alert.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(alert)
        return alert

    async def resolve_alert(self, alert_id: int, user_id: int) -> Alert:
        alert = await self.get_alert(alert_id, user_id)
        alert.status = AlertStatus.RESOLVED
        alert.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(alert)
        return alert

    async def check_location_alerts(self, device_id: int, location: Any) -> None:
        query = select(Device).where(Device.id == device_id)
        result = await self.db.execute(query)
        device = result.scalar_one_or_none()
        if not device:
            raise NotFoundError("Device not found")

        if device.battery_level is not None and device.battery_level < 20:
            await self.create_alert(
                user_id=device.user_id,
                device_id=device.id,
                alert_type=AlertType.LOW_BATTERY,
                title="Low battery",
                message=f"Device {device.device_name} battery is below 20%.",
                data=str({"battery": device.battery_level}),
            )

    async def create_alert(
        self,
        user_id: int,
        device_id: int | None,
        alert_type: AlertType,
        title: str,
        message: str,
        data: str | None = None,
    ) -> Alert:
        alert = Alert(
            user_id=user_id,
            device_id=device_id,
            type=alert_type,
            title=title,
            message=message,
            status=AlertStatus.PENDING,
            data=data,
            created_at=datetime.utcnow(),
        )
        self.db.add(alert)
        await self.db.commit()
        await self.db.refresh(alert)
        return alert
