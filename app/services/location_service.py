from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from sqlalchemy.sql import text
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json
from geoalchemy2.functions import ST_SetSRID
from geoalchemy2.elements import WKTElement

from app.models.location import Location
from app.models.device import Device, DeviceStatus
from app.schemas.location import LocationCreate, LocationResponse
from app.core.exceptions import NotFoundError, ForbiddenError
from app.services.cache_service import CacheService
from app.services.alert_service import AlertService
from app.services.geofence_service import GeofenceService


class LocationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.cache = CacheService()
        self.alert_service = AlertService(db)
        self.geofence_service = GeofenceService(db)

    async def store_location(self, device_uuid: str, location_data: LocationCreate) -> Location:
        """Store a new GPS location from mobile device"""
        # Get device
        query = select(Device).where(Device.device_uuid == device_uuid)
        result = await self.db.execute(query)
        device = result.scalar_one_or_none()
        
        if not device:
            raise NotFoundError("Device not found")
        
        # Update device status
        device.battery_level = location_data.battery
        device.last_connection = datetime.utcnow()
        device.status = DeviceStatus.LOST if device.lost_mode else DeviceStatus.ONLINE
        
        # Create location with PostGIS point
        point = WKTElement(f'POINT({location_data.longitude} {location_data.latitude})', srid=4326)
        timestamp = location_data.timestamp or datetime.utcnow()
        
        location = Location(
            device_id=device.id,
            latitude=location_data.latitude,
            longitude=location_data.longitude,
            altitude=location_data.altitude,
            accuracy=location_data.accuracy,
            speed=location_data.speed,
            battery=location_data.battery,
            point=point,
            timestamp=timestamp
        )
        
        self.db.add(location)
        await self.db.commit()
        await self.db.refresh(location)
        
        # Cache last location
        await self.cache.set_last_location(device.id, {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "timestamp": location.timestamp.isoformat(),
            "speed": location.speed,
            "battery": location.battery
        })
        
        # Check for alerts
        await self.alert_service.check_location_alerts(device.id, location)
        
        return location

    async def get_last_location(self, device_id: int, user_id: int) -> dict | Location | None:
        """Get the last known location for a device"""
        # Verify device ownership first
        device_query = select(Device).where(
            and_(Device.id == device_id, Device.user_id == user_id)
        )
        device_result = await self.db.execute(device_query)
        if not device_result.scalar_one_or_none():
            raise ForbiddenError("Device access denied")

        # Check cache first
        cached = await self.cache.get_last_location(device_id)
        if cached:
            return cached
        
        # Query database
        query = select(Location).where(
            Location.device_id == device_id
        ).order_by(desc(Location.timestamp)).limit(1)
        result = await self.db.execute(query)
        location = result.scalar_one_or_none()
        
        if location:
            await self.cache.set_last_location(device_id, {
                "id": location.id,
                "device_id": location.device_id,
                "latitude": location.latitude,
                "longitude": location.longitude,
                "altitude": location.altitude,
                "accuracy": location.accuracy,
                "speed": location.speed,
                "battery": location.battery,
                "timestamp": location.timestamp.isoformat() if location.timestamp else None,
                "created_at": location.created_at.isoformat() if location.created_at else None,
            })
            return location

        raise NotFoundError("No location found for this device")

    async def get_location_history(
        self,
        device_id: int,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        limit: int = 1000
    ) -> List[Location]:
        """Get location history for a device"""
        # Verify device belongs to user
        query = select(Device).where(
            and_(Device.id == device_id, Device.user_id == user_id)
        )
        result = await self.db.execute(query)
        if not result.scalar_one_or_none():
            raise ForbiddenError("Device access denied")
        
        query = select(Location).where(
            and_(
                Location.device_id == device_id,
                Location.timestamp >= start_date,
                Location.timestamp <= end_date
            )
        ).order_by(Location.timestamp).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_route_geojson(self, device_id: int, user_id: int) -> Dict[str, Any]:
        """Get route as GeoJSON"""
        # Verify device belongs to user
        query = select(Device).where(
            and_(Device.id == device_id, Device.user_id == user_id)
        )
        result = await self.db.execute(query)
        if not result.scalar_one_or_none():
            raise ForbiddenError("Device access denied")
        
        # Build GeoJSON using PostGIS
        sql = text("""
            SELECT ST_AsGeoJSON(
                ST_SetSRID(
                    ST_MakeLine(point ORDER BY timestamp),
                    4326
                )
            ) as geojson
            FROM locations
            WHERE device_id = :device_id
            AND timestamp >= NOW() - INTERVAL '24 hours'
        """)
        
        result = await self.db.execute(sql, {"device_id": device_id})
        geojson_data = result.scalar_one_or_none()
        
        if geojson_data:
            return json.loads(geojson_data)
        return {"type": "LineString", "coordinates": []}

    async def find_nearby_devices(
        self,
        latitude: float,
        longitude: float,
        radius: float,
        user_id: int
    ) -> List[Dict[str, Any]]:
        """Find devices near a location"""
        point = WKTElement(f'POINT({longitude} {latitude})', srid=4326)
        
        sql = text("""
            SELECT 
                d.id,
                d.device_name,
                d.device_uuid,
                l.latitude,
                l.longitude,
                l.timestamp,
                ST_Distance(l.point, ST_SetSRID(:point, 4326)) as distance
            FROM devices d
            JOIN locations l ON l.device_id = d.id
            WHERE d.user_id = :user_id
            AND d.is_active = true
            AND ST_DWithin(l.point, ST_SetSRID(:point, 4326), :radius)
            AND l.timestamp >= NOW() - INTERVAL '1 hour'
            ORDER BY distance
        """)
        
        result = await self.db.execute(sql, {
            "point": point,
            "user_id": user_id,
            "radius": radius
        })
        
        rows = result.fetchall()
        return [
            {
                "device_id": row[0],
                "device_name": row[1],
                "device_uuid": row[2],
                "latitude": row[3],
                "longitude": row[4],
                "timestamp": row[5],
                "distance": row[6]
            }
            for row in rows
        ]

    async def get_statistics(self, device_id: int, user_id: int) -> Dict[str, Any]:
        """Get location statistics for a device"""
        # Verify device belongs to user
        query = select(Device).where(
            and_(Device.id == device_id, Device.user_id == user_id)
        )
        result = await self.db.execute(query)
        if not result.scalar_one_or_none():
            raise ForbiddenError("Device access denied")
        
        # Get statistics
        sql = text("""
            SELECT 
                COUNT(*) as total_locations,
                MIN(timestamp) as first_location,
                MAX(timestamp) as last_location,
                AVG(speed) as avg_speed,
                MAX(speed) as max_speed,
                AVG(battery) as avg_battery,
                ST_Length(ST_MakeLine(point ORDER BY timestamp)) as total_distance
            FROM locations
            WHERE device_id = :device_id
            AND timestamp >= NOW() - INTERVAL '24 hours'
        """)
        
        result = await self.db.execute(sql, {"device_id": device_id})
        stats = result.fetchone()
        
        return {
            "total_locations": stats[0] or 0,
            "first_location": stats[1],
            "last_location": stats[2],
            "avg_speed": stats[3] or 0,
            "max_speed": stats[4] or 0,
            "avg_battery": stats[5] or 0,
            "total_distance": stats[6] or 0
        }