import json
from app.database.redis import redis_client


class CacheService:
    def __init__(self):
        self.redis = redis_client

    async def set_device_info(self, device_id: int, data: dict) -> None:
        await self.redis.set(f"device:{device_id}:info", json.dumps(data), expire=3600)

    async def get_device_info(self, device_id: int) -> dict | None:
        raw = await self.redis.get(f"device:{device_id}:info")
        return json.loads(raw) if raw else None

    async def delete_device_info(self, device_id: int) -> None:
        await self.redis.delete(f"device:{device_id}:info")

    async def set_last_location(self, device_id: int, data: dict) -> None:
        await self.redis.set(f"device:{device_id}:last_location", json.dumps(data), expire=3600)

    async def get_last_location(self, device_id: int) -> dict | None:
        raw = await self.redis.get(f"device:{device_id}:last_location")
        return json.loads(raw) if raw else None

    async def set_device_status(self, device_id: int, data: dict) -> None:
        await self.redis.set(f"device:{device_id}:status", json.dumps(data), expire=300)

    async def get_device_status(self, device_id: int) -> dict | None:
        raw = await self.redis.get(f"device:{device_id}:status")
        return json.loads(raw) if raw else None
