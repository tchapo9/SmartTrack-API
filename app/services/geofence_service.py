from datetime import datetime
from typing import Any, List, Optional
import math

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from geoalchemy2.elements import WKTElement

from app.models.geofence import Geofence
from app.models.device import Device
from app.schemas.geofence import GeofenceCreate
from app.core.exceptions import NotFoundError, ForbiddenError
from app.services.alert_service import AlertService
from app.models.alert import AlertType


class GeofenceService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.alert_service = AlertService(db)

    async def create_geofence(self, user_id: int, geofence_data: GeofenceCreate) -> Geofence:
        geofence = Geofence(
            user_id=user_id,
            device_id=geofence_data.device_id,
            name=geofence_data.name,
            description=geofence_data.description,
            latitude=geofence_data.latitude,
            longitude=geofence_data.longitude,
            radius=geofence_data.radius,
            point=WKTElement(f"POINT({geofence_data.longitude} {geofence_data.latitude})", srid=4326),
            is_active=True,
            created_at=datetime.utcnow(),
        )
        self.db.add(geofence)
        await self.db.commit()
        await self.db.refresh(geofence)
        return geofence

    async def list_geofences(self, user_id: int) -> List[Geofence]:
        query = select(Geofence).where(Geofence.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_geofence(self, geofence_id: int, user_id: int) -> Geofence:
        query = select(Geofence).where(
            and_(Geofence.id == geofence_id, Geofence.user_id == user_id)
        )
        result = await self.db.execute(query)
        geofence = result.scalar_one_or_none()
        if not geofence:
            raise NotFoundError("Geofence not found")
        return geofence

    async def update_geofence(self, geofence_id: int, user_id: int, geofence_data: GeofenceCreate) -> Geofence:
        geofence = await self.get_geofence(geofence_id, user_id)
        for field, value in geofence_data.dict(exclude_unset=True).items():
            if field in {"latitude", "longitude"} and value is not None:
                setattr(geofence, field, value)
            elif field != "latitude" and field != "longitude":
                setattr(geofence, field, value)

        if geofence_data.latitude is not None or geofence_data.longitude is not None:
            geofence.point = WKTElement(f"POINT({geofence.longitude} {geofence.latitude})", srid=4326)

        geofence.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(geofence)
        return geofence

    async def delete_geofence(self, geofence_id: int, user_id: int) -> None:
        geofence = await self.get_geofence(geofence_id, user_id)
        await self.db.delete(geofence)
        await self.db.commit()

    async def check_location_geofences(self, device: Device, location: Any) -> None:
        query = select(Geofence).where(
            and_(
                Geofence.user_id == device.user_id,
                Geofence.is_active.is_(True),
                or_(Geofence.device_id.is_(None), Geofence.device_id == device.id),
            )
        )
        result = await self.db.execute(query)
        geofences = result.scalars().all()

        for geofence in geofences:
            distance = self._haversine(
                location.latitude,
                location.longitude,
                geofence.latitude,
                geofence.longitude,
            )
            inside = distance <= geofence.radius
            alert_type = AlertType.GEOFENCE_ENTER if inside else AlertType.GEOFENCE_EXIT
            await self.alert_service.create_alert(
                user_id=device.user_id,
                device_id=device.id,
                alert_type=alert_type,
                title=f"Geofence {'entered' if inside else 'exited'}: {geofence.name}",
                message=(
                    f"Device {device.device_name} "
                    f"{'entered' if inside else 'exited'} geofence '{geofence.name}' "
                    f"at distance {distance:.1f}m."
                ),
                data=str({
                    "geofence_id": geofence.id,
                    "distance": distance,
                    "inside": inside,
                }),
            )

    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        r = 6371000.0
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        return 2 * r * math.asin(math.sqrt(a))
