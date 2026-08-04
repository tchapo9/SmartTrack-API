from typing import Dict, List
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, device_id: int, websocket: WebSocket):
        connections = self.active_connections.setdefault(device_id, [])
        connections.append(websocket)

    async def disconnect(self, device_id: int, websocket: WebSocket):
        connections = self.active_connections.get(device_id, [])
        if websocket in connections:
            connections.remove(websocket)
        if not connections and device_id in self.active_connections:
            self.active_connections.pop(device_id, None)

    async def broadcast_to_device(self, device_id: int, message: dict):
        connections = self.active_connections.get(device_id, [])
        for connection in connections:
            await connection.send_json(message)

    async def list_connections(self, device_id: int) -> List[WebSocket]:
        return self.active_connections.get(device_id, [])
