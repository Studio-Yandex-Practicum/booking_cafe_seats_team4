from functools import wraps
import asyncio
import json
from typing import Callable, Type, TypeVar, Optional, Any
from core.redis import redis_cache

T = TypeVar('T')


def cache_response(
    cache_key_template: Optional[str] = None,
    expire: int = 600,
    response_model: Optional[Type[T]] = None
):
    def decorator(function: Callable) -> Callable:
        @wraps(function)
        async def wrapper(*args, **kwargs) -> Any:
            if cache_key_template:
                cache_key = cache_key_template.format(**kwargs)
            else:
                cache_key = f"{function.__module__}:{function.__name__}"
            cached_json = await redis_cache.get_cached_data(cache_key)
            if cached_json is not None:
                if response_model and cached_json:
                    try:
                        cached_data = json.loads(cached_json)
                        if isinstance(cached_data, list):
                            return [
                                response_model.model_validate(
                                    item) for item in cached_data]
                        else:
                            return response_model.model_validate(cached_data)
                    except json.JSONDecodeError:
                        return cached_json
                return cached_json
            result = await function(*args, **kwargs)
            if response_model and result:
                if isinstance(result, list):
                    cache_data = [item.model_dump(
                        mode='json') for item in result]
                else:
                    cache_data = result.model_dump(mode='json')
                cache_value = json.dumps(cache_data)
            else:
                cache_value = result
            asyncio.create_task(
                redis_cache.set_cached_data(
                    cache_key, cache_value, expire=expire)
            )

            return result
        return wrapper
    return decorator
