from datetime import datetime, timedelta
from typing import Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.device import Device
from app.models.alert import Alert, AlertStatus
from app.models.location import Location
from app.core.exceptions import NotFoundError


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_overview(self, user_id: int) -> Dict[str, object]:
        total_devices = await self.db.scalar(select(func.count(Device.id)).where(Device.user_id == user_id))
        active_devices = await self.db.scalar(
            select(func.count(Device.id)).where(Device.user_id == user_id, Device.is_active.is_(True))
        )
        lost_devices = await self.db.scalar(
            select(func.count(Device.id)).where(Device.user_id == user_id, Device.lost_mode.is_(True))
        )
        pending_alerts = await self.db.scalar(
            select(func.count(Alert.id)).where(Alert.user_id == user_id, Alert.status == AlertStatus.PENDING)
        )
        latest_location = await self.db.execute(
            select(Location.device_id, Location.timestamp)
            .join(Device, Device.id == Location.device_id)
            .where(Device.user_id == user_id)
            .order_by(Location.timestamp.desc())
            .limit(1)
        )
        latest_location = latest_location.fetchone()

        return {
            "total_devices": total_devices or 0,
            "active_devices": active_devices or 0,
            "lost_devices": lost_devices or 0,
            "pending_alerts": pending_alerts or 0,
            "latest_location": {
                "device_id": latest_location[0],
                "timestamp": latest_location[1],
            } if latest_location else None,
            "since": datetime.utcnow().isoformat(),
        }

    async def get_device_summary(self, device_id: int, user_id: int) -> Dict[str, object]:
        device = await self.db.get(Device, device_id)
        if not device or device.user_id != user_id:
            raise NotFoundError("Device not found")

        last_location = await self.db.execute(
            select(Location)
            .where(Location.device_id == device_id)
            .order_by(Location.timestamp.desc())
            .limit(1)
        )
        last_location = last_location.scalar_one_or_none()

        return {
            "device_id": device.id,
            "device_name": device.device_name,
            "status": device.status.value,
            "battery_level": device.battery_level,
            "lost_mode": device.lost_mode,
            "last_location": {
                "latitude": last_location.latitude,
                "longitude": last_location.longitude,
                "timestamp": last_location.timestamp,
            } if last_location else None,
        }
