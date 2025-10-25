from functools import wraps
from typing import Callable, Type, TypeVar
from fastapi.encoders import jsonable_encoder
from core.redis import redis_cache

T = TypeVar('T')


def cache_response(
    cache_key_template: str,
    expire: int = 600,
    response_model: Type[T] = None
):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            redis_client = kwargs.get('redis_client')
            if not redis_client:
                raise ValueError("redis_client must be provided")
            cache_key = cache_key_template.format(**kwargs)
            cached_data = await redis_cache.get_cached_data(cache_key)
            if cached_data:
                if response_model:
                    return [response_model(**item) for item in cached_data]
                return cached_data
            result = await func(*args, **kwargs)
            result_data = jsonable_encoder(result)
            await redis_cache.set_cached_data(
                cache_key, result_data, expire=expire
            )
            return result
        return wrapper
    return decorator
