from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import Optional
import logging
import uvicorn

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.exceptions import handle_exceptions
from app.database.connection import engine, Base
from app.database.redis import redis_client
from app.websocket.connection_manager import ConnectionManager
from app.websocket.tracking_handler import TrackingWebSocket

# Import routers
from app.routers import (
    auth, users, devices, locations, 
    tracking, alerts, geofence, dashboard, admin
)

# Setup logging
logger = setup_logging()

# Initialize WebSocket manager
manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    logger.info("Starting SmartTrack API...")
    await redis_client.initialize()
    logger.info("Redis connection established")
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created/verified")
    
    yield
    
    # Shutdown
    logger.info("Shutting down SmartTrack API...")
    await redis_client.close()
    await engine.dispose()
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Real-time GPS Tracking API for SmartTrack application",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.DEBUG else settings.CORS_ORIGINS
)

# Register exception handlers
app.add_exception_handler(RequestValidationError, handle_exceptions)
app.add_exception_handler(Exception, handle_exceptions)

# Include routers
app.include_router(auth, prefix="/api/auth", tags=["Authentication"])
app.include_router(users, prefix="/api/users", tags=["Users"])
app.include_router(devices, prefix="/api/devices", tags=["Devices"])
app.include_router(locations, prefix="/api/locations", tags=["Locations"])
app.include_router(tracking, prefix="/api/tracking", tags=["Tracking"])
app.include_router(alerts, prefix="/api/alerts", tags=["Alerts"])
app.include_router(geofence, prefix="/api/geofence", tags=["Geofencing"])
app.include_router(dashboard, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(admin, prefix="/api/admin", tags=["Administration"])


# WebSocket endpoint
@app.websocket("/ws/tracking/{device_id}")
async def websocket_tracking(websocket: WebSocket, device_id: int):
    """WebSocket endpoint for real-time GPS tracking"""
    tracking_handler = TrackingWebSocket(websocket, device_id, manager)
    await tracking_handler.handle_connection()


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to SmartTrack API",
        "docs": "/api/docs",
        "redoc": "/api/redoc",
        "version": settings.APP_VERSION
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info"
    )    from urllib.parse import urlparse
    
    def get_allowed_hosts():
        if settings.DEBUG:
            return ["*"]
        hosts = []
        for origin in settings.CORS_ORIGINS:
            parsed = urlparse(origin)
            hosts.append(parsed.hostname or origin)
        return list(dict.fromkeys(hosts))
    
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=get_allowed_hosts()
    )