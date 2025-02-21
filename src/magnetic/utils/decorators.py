"""Utility decorators for the application."""

import functools
from typing import Any, Callable, Optional, Union
from datetime import timedelta

from ..services.cache import cache

def cached(
    expire: Optional[Union[int, timedelta]] = None,
    key_prefix: str = ""
) -> Callable:
    """
    Cache decorator for API endpoints and functions.
    
    Args:
        expire: Cache expiration time in seconds or timedelta
        key_prefix: Prefix for cache key
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}"
            if args:
                cache_key += f":{':'.join(str(a) for a in args)}"
            if kwargs:
                cache_key += f":{':'.join(f'{k}={v}' for k, v in sorted(kwargs.items()))}"
            
            # Try to get from cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, expire=expire)
            return result
            
        return wrapper
    return decorator 