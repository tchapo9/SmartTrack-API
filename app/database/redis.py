from redis.asyncio import Redis
from app.core.config import settings


class RedisClient:
    def __init__(self):
        self._client: Redis | None = None

    async def initialize(self):
        self._client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        await self._client.ping()

    async def close(self):
        if self._client:
            await self._client.close()

    def get_client(self) -> Redis:
        if self._client is None:
            raise RuntimeError("Redis client is not initialized")
        return self._client

    async def set(self, key: str, value, expire: int | None = None):
        client = self.get_client()
        await client.set(key, value, ex=expire)

    async def get(self, key: str):
        client = self.get_client()
        return await client.get(key)

    async def delete(self, key: str):
        client = self.get_client()
        await client.delete(key)


redis_client = RedisClient()
