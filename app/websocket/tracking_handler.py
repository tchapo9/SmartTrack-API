from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio
from datetime import datetime
from typing import Dict, Any
import logging

from app.websocket.connection_manager import ConnectionManager
from app.database.connection import AsyncSessionLocal
from app.services.location_service import LocationService
from app.services.device_service import DeviceService
from app.schemas.location import LocationCreate
from app.core.exceptions import NotFoundError

logger = logging.getLogger(__name__)


class TrackingWebSocket:
    def __init__(self, websocket: WebSocket, device_id: int, manager: ConnectionManager):
        self.websocket = websocket
        self.device_id = device_id
        self.manager = manager
        self.is_connected = False

    async def handle_connection(self):
        """Handle WebSocket connection"""
        try:
            await self.websocket.accept()
            await self.manager.connect(self.device_id, self.websocket)
            self.is_connected = True
            
            logger.info(f"WebSocket connected for device {self.device_id}")
            
            # Send initial status
            await self.send_initial_status()
            
            # Handle messages
            while self.is_connected:
                try:
                    data = await self.websocket.receive_text()
                    await self.handle_message(data)
                except WebSocketDisconnect:
                    await self.handle_disconnect()
                    break
                except Exception as e:
                    logger.error(f"Error handling WebSocket message: {str(e)}")
                    await self.send_error(str(e))
        
        except Exception as e:
            logger.error(f"WebSocket connection error: {str(e)}")
            await self.handle_disconnect()

    async def handle_message(self, data: str):
        """Handle incoming WebSocket messages"""
        try:
            message = json.loads(data)
            message_type = message.get("type")
            
            if message_type == "location":
                await self.handle_location_update(message.get("data", {}))
            elif message_type == "ping":
                await self.send_pong()
            elif message_type == "subscribe":
                await self.handle_subscription(message.get("data", {}))
            elif message_type == "command":
                await self.handle_command(message.get("data", {}))
            else:
                await self.send_error(f"Unknown message type: {message_type}")
        
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format")
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            await self.send_error(str(e))

    async def handle_location_update(self, data: Dict[str, Any]):
        """Handle location update from mobile device"""
        try:
            # Process location
            location_data = LocationCreate(
                device_uuid=data.get("device_uuid"),
                latitude=data.get("latitude"),
                longitude=data.get("longitude"),
                altitude=data.get("altitude"),
                accuracy=data.get("accuracy"),
                speed=data.get("speed"),
                battery=data.get("battery"),
                timestamp=data.get("timestamp")
            )
            
            # Store location in database
            async with AsyncSessionLocal() as db:
                service = LocationService(db)
                location = await service.store_location(
                    device_uuid=data.get("device_uuid"),
                    location_data=location_data
                )
                
                # Broadcast to all clients watching this device
                await self.manager.broadcast_to_device(
                    self.device_id,
                    {
                        "type": "location_update",
                        "data": {
                            "latitude": location.latitude,
                            "longitude": location.longitude,
                            "timestamp": location.timestamp.isoformat(),
                            "speed": location.speed,
                            "battery": location.battery
                        }
                    }
                )
        
        except Exception as e:
            logger.error(f"Error handling location update: {str(e)}")
            await self.send_error(f"Location update failed: {str(e)}")

    async def handle_subscription(self, data: Dict[str, Any]):
        """Handle subscription requests"""
        # Implement subscription logic if needed
        pass

    async def handle_command(self, data: Dict[str, Any]):
        """Handle device commands"""
        # Implement command handling logic
        pass

    async def send_initial_status(self):
        """Send initial device status"""
        try:
            async with AsyncSessionLocal() as db:
                service = DeviceService(db)
                status = await service.get_device_status(self.device_id, None)  # Should get user_id from token
                
                await self.websocket.send_json({
                    "type": "initial_status",
                    "data": status
                })
        except Exception as e:
            logger.error(f"Error sending initial status: {str(e)}")

    async def send_pong(self):
        """Send pong response"""
        await self.websocket.send_json({
            "type": "pong",
            "timestamp": datetime.utcnow().isoformat()
        })

    async def send_error(self, message: str):
        """Send error message to client"""
        await self.websocket.send_json({
            "type": "error",
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def send_position_update(self, location_data: Dict[str, Any]):
        """Send position update to client"""
        await self.websocket.send_json({
            "type": "position_update",
            "data": location_data,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def handle_disconnect(self):
        """Handle disconnection"""
        self.is_connected = False
        await self.manager.disconnect(self.device_id, self.websocket)
        logger.info(f"WebSocket disconnected for device {self.device_id}")