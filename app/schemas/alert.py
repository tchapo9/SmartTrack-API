from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class AlertType(str, Enum):
    LOW_BATTERY = "low_battery"
    GEOFENCE_EXIT = "geofence_exit"
    GEOFENCE_ENTER = "geofence_enter"
    DEVICE_OFFLINE = "device_offline"
    MOVEMENT_DETECTED = "movement_detected"
    SPEED_EXCEEDED = "speed_exceeded"
    LOST_MODE = "lost_mode"


class AlertStatus(str, Enum):
    PENDING = "pending"
    READ = "read"
    RESOLVED = "resolved"


class AlertCreate(BaseModel):
    device_id: Optional[int] = None
    type: AlertType
    title: str = Field(..., max_length=100)
    message: str = Field(..., max_length=500)
    data: Optional[str] = None


class AlertResponse(BaseModel):
    id: int
    user_id: int
    device_id: Optional[int] = None
    type: AlertType
    title: str
    message: str
    status: AlertStatus
    data: Optional[str] = None
    read_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
