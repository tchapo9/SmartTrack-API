from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class LocationCreate(BaseModel):
    device_uuid: str
    latitude: float
    longitude: float
    altitude: Optional[float] = None
    accuracy: Optional[float] = None
    speed: Optional[float] = None
    battery: Optional[float] = None
    timestamp: Optional[datetime] = None


class LocationResponse(BaseModel):
    id: int
    device_id: int
    latitude: float
    longitude: float
    altitude: Optional[float] = None
    accuracy: Optional[float] = None
    speed: Optional[float] = None
    battery: Optional[float] = None
    timestamp: datetime
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
