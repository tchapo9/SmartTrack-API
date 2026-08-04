from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
from app.models.device import Device
from app.services.location_service import LocationService


class TrackingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.location_service = LocationService(db)

    async def send_location_update(self, device_uuid: str, location_data: Dict[str, Any]):
        return await self.location_service.store_location(device_uuid, location_data)
