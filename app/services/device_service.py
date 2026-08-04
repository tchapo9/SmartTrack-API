from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from app.models.device import Device, DeviceStatus
from app.models.location import Location
from app.schemas.device import DeviceCreate, DeviceUpdate
from app.core.exceptions import NotFoundError, ForbiddenError, ConflictError
from app.services.cache_service import CacheService


class DeviceService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.cache = CacheService()

    async def register_device(self, user_id: int, device_data: DeviceCreate) -> Device:
        """Register a new device"""
        # Check if device already exists
        existing = await self.get_device_by_uuid(device_data.device_uuid)
        if existing:
            raise ConflictError("Device already registered")
        
        device = Device(
            user_id=user_id,
            device_name=device_data.device_name,
            device_uuid=device_data.device_uuid,
            android_version=device_data.android_version,
            model=device_data.model,
            battery_level=100.0,
            status=DeviceStatus.OFFLINE,
            is_active=True
        )
        
        self.db.add(device)
        await self.db.commit()
        await self.db.refresh(device)
        
        # Cache device info
        await self.cache.set_device_info(device.id, device_data.dict())
        
        return device

    async def get_user_devices(self, user_id: int) -> List[Device]:
        """Get all devices for a user"""
        query = select(Device).where(Device.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_device(self, device_id: int, user_id: int | None = None) -> Device:
        """Get device by ID, optionally verifying ownership."""
        query = select(Device).where(Device.id == device_id)
        if user_id is not None:
            query = query.where(Device.user_id == user_id)

        result = await self.db.execute(query)
        device = result.scalar_one_or_none()
        
        if not device:
            raise NotFoundError("Device not found")
        
        return device

    async def get_device_by_uuid(self, device_uuid: str) -> Optional[Device]:
        """Get device by UUID"""
        query = select(Device).where(Device.device_uuid == device_uuid)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_device(self, device_id: int, user_id: int, device_data: DeviceUpdate) -> Device:
        """Update device information"""
        device = await self.get_device(device_id, user_id)
        
        for field, value in device_data.dict(exclude_unset=True).items():
            setattr(device, field, value)
        
        device.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(device)
        
        # Update cache
        await self.cache.set_device_info(device_id, device_data.dict())
        
        return device

    async def delete_device(self, device_id: int, user_id: int) -> None:
        """Delete a device"""
        device = await self.get_device(device_id, user_id)
        
        await self.db.delete(device)
        await self.db.commit()
        
        # Clear cache
        await self.cache.delete_device_info(device_id)

    async def activate_device(self, device_id: int, user_id: int) -> Device:
        """Activate device tracking"""
        device = await self.get_device(device_id, user_id)
        device.is_active = True
        device.status = DeviceStatus.ONLINE
        device.last_connection = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(device)
        return device

    async def deactivate_device(self, device_id: int, user_id: int) -> Device:
        """Deactivate device tracking"""
        device = await self.get_device(device_id, user_id)
        device.is_active = False
        device.status = DeviceStatus.INACTIVE
        
        await self.db.commit()
        await self.db.refresh(device)
        return device

    async def set_lost_mode(self, device_id: int, user_id: int, enable: bool) -> Device:
        """Enable or disable lost mode for a device"""
        device = await self.get_device(device_id, user_id)
        device.lost_mode = enable
        device.status = DeviceStatus.LOST if enable else DeviceStatus.ONLINE
        device.last_connection = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(device)
        return device

    async def get_device_status(self, device_id: int, user_id: int | None = None) -> Dict[str, Any]:
        """Get device status information"""
        device = await self.get_device(device_id, user_id)
        
        # Get last location
        query = select(Location).where(
            Location.device_id == device_id
        ).order_by(desc(Location.timestamp)).limit(1)
        result = await self.db.execute(query)
        last_location = result.scalar_one_or_none()
        
        # Calculate online status
        is_online = False
        if device.last_connection:
            time_since_last = datetime.utcnow() - device.last_connection
            is_online = time_since_last.total_seconds() < 300  # 5 minutes threshold
        
        return {
            "device_id": device.id,
            "device_name": device.device_name,
            "is_online": is_online,
            "status": device.status.value,
            "battery_level": device.battery_level,
            "last_connection": device.last_connection,
            "last_location": {
                "latitude": last_location.latitude if last_location else None,
                "longitude": last_location.longitude if last_location else None,
                "timestamp": last_location.timestamp if last_location else None
            } if last_location else None
        }

    async def update_device_status(self, device_uuid: str, status_data: Dict[str, Any]) -> None:
        """Update device status (called from mobile app)"""
        device = await self.get_device_by_uuid(device_uuid)
        if not device:
            raise NotFoundError("Device not found")
        
        if "battery_level" in status_data:
            device.battery_level = status_data["battery_level"]
        
        if "status" in status_data:
            device.status = DeviceStatus(status_data["status"])
        
        device.last_connection = datetime.utcnow()
        
        await self.db.commit()
        
        # Update cache
        await self.cache.set_device_status(device.id, {
            "battery": device.battery_level,
            "status": device.status.value,
            "last_connection": device.last_connection.isoformat()
        })