from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.connection import Base
import enum


class AlertType(str, enum.Enum):
    LOW_BATTERY = "low_battery"
    GEOFENCE_EXIT = "geofence_exit"
    GEOFENCE_ENTER = "geofence_enter"
    DEVICE_OFFLINE = "device_offline"
    MOVEMENT_DETECTED = "movement_detected"
    SPEED_EXCEEDED = "speed_exceeded"
    LOST_MODE = "lost_mode"


class AlertStatus(str, enum.Enum):
    PENDING = "pending"
    READ = "read"
    RESOLVED = "resolved"


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=True, index=True)
    type = Column(Enum(AlertType), nullable=False)
    title = Column(String(100), nullable=False)
    message = Column(String(500), nullable=False)
    status = Column(Enum(AlertStatus), default=AlertStatus.PENDING)
    data = Column(String(500), nullable=True)  # Additional data as JSON string
    read_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="alerts")
    device = relationship("Device", back_populates="alerts")