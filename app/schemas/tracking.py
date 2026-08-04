from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class TrackingMessage(BaseModel):
    type: str
    data: dict


class TrackingResponse(BaseModel):
    device_id: int
    latitude: float
    longitude: float
    timestamp: datetime
    speed: Optional[float] = None
    battery: Optional[float] = None


class CurrentPositionResponse(BaseModel):
    device_id: int
    latitude: float
    longitude: float
    timestamp: datetime
    speed: Optional[float] = None
    battery: Optional[float] = None

    class Config:
        orm_mode = True
