from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class DeviceCreate(BaseModel):
    device_name: str = Field(..., max_length=100)
    device_uuid: str = Field(..., max_length=255)
    android_version: Optional[str] = None
    model: Optional[str] = None


class DeviceUpdate(BaseModel):
    device_name: Optional[str] = Field(None, max_length=100)
    android_version: Optional[str] = None
    model: Optional[str] = None
    is_active: Optional[bool] = None
    lost_mode: Optional[bool] = None


class DeviceResponse(BaseModel):
    id: int
    user_id: int
    device_name: str
    device_uuid: str
    android_version: Optional[str]
    model: Optional[str]
    battery_level: float
    status: str
    is_active: bool
    lost_mode: bool
    last_connection: Optional[datetime]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True
