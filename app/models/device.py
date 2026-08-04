from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.connection import Base
import enum


class DeviceStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    INACTIVE = "inactive"
    LOST = "lost"


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_name = Column(String(100), nullable=False)
    device_uuid = Column(String(255), unique=True, nullable=False, index=True)
    android_version = Column(String(20), nullable=True)
    model = Column(String(100), nullable=True)
    battery_level = Column(Float, default=0.0)
    status = Column(Enum(DeviceStatus), default=DeviceStatus.OFFLINE)
    is_active = Column(Boolean, default=True)
    last_connection = Column(DateTime(timezone=True), nullable=True)
    lost_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="devices")
    locations = relationship("Location", back_populates="device", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="device", cascade="all, delete-orphan")