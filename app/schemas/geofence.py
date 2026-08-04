from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class GeofenceCreate(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    latitude: float
    longitude: float
    radius: float
    device_id: Optional[int] = None


class GeofenceResponse(BaseModel):
    id: int
    user_id: int
    device_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    latitude: float
    longitude: float
    radius: float
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
