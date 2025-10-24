import json
import logging
from typing import Any, Optional

import redis.asyncio as redis

from core.config import settings

logger = logging.getLogger(__name__)


class RedisCache:
    def __init__(self):
        self.redis: Optional[redis.Redis] = None

    async def init_redis(self) -> redis.Redis:
        """Инициализация Redis подключения."""

        try:
            self.redis = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
                retry_on_timeout=True
            )
            await self.redis.ping()
            logger.info("Redis connection established")
            return self.redis
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise

    async def get_redis(self) -> redis.Redis:
        """Получение Redis клиента."""

        if self.redis is None:
            await self.init_redis()
        return self.redis

    async def close_redis(self):
        """Закрытие Redis подключения."""

        if self.redis:
            await self.redis.close()
            logger.info("Redis connection closed")

    async def get_cached_data(self, key: str) -> Optional[Any]:
        """Получение данных из кэша."""

        try:
            redis_client = await self.get_redis()
            cached = await redis_client.get(key)
            if cached:
                return json.loads(cached)
            return None
        except Exception as e:
            logger.warning(
                f"Error getting cached data for key {key}: {str(e)}")
            return None

    async def set_cached_data(self, key: str, data: Any, expire: int = 300):
        """Сохранение данных в кэш."""

        try:
            redis_client = await self.get_redis()
            await redis_client.setex(
                key,
                expire,
                json.dumps(data, default=str)
            )
        except Exception as e:
            logger.warning(
                f"Error setting cached data for key {key}: {str(e)}")

    async def delete_pattern(self, pattern: str):
        """Удаление ключей по шаблону."""

        try:
            redis_client = await self.get_redis()
            keys = await redis_client.keys(pattern)
            if keys:
                await redis_client.delete(*keys)
                logger.info(
                    f"Deleted {len(keys)} keys with pattern: {pattern}")
        except Exception as e:
            logger.error(
                f"Error deleting keys with pattern {pattern}: {str(e)}")


redis_cache = RedisCache()


async def get_redis() -> redis.Redis:
    """Зависимость для получения Redis клиента."""

    return await redis_cache.get_redis()
