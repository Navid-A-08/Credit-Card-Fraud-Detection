import redis.asyncio as redis
from typing import Optional, Any
import json
from app.config import settings


class RedisClient:
    def __init__(self):
        self.redis: Optional[redis.Redis] = None

    async def connect(self):
        self.redis = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        await self.redis.ping()
        print("Connected to Redis")

    async def disconnect(self):
        if self.redis:
            await self.redis.close()
            print("Disconnected from Redis")

    async def get(self, key: str) -> Optional[str]:
        return await self.redis.get(key)

    async def set(self, key: str, value: str, ttl: int = None):
        ttl = ttl or settings.REDIS_CACHE_TTL
        await self.redis.set(key, value, ex=ttl)

    async def delete(self, key: str):
        await self.redis.delete(key)

    async def publish(self, channel: str, message: dict):
        await self.redis.publish(channel, json.dumps(message))

    async def subscribe(self, *channels: str):
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(*channels)
        return pubsub

    async def increment(self, key: str, amount: int = 1) -> int:
        return await self.redis.incrby(key, amount)

    async def get_counter(self, key: str) -> int:
        value = await self.redis.get(key)
        return int(value) if value else 0


redis_client = RedisClient()


async def get_redis() -> RedisClient:
    return redis_client
