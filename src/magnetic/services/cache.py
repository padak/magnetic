"""Redis cache service implementation."""

import json
from typing import Any, Optional, Union
from datetime import timedelta

import redis.asyncio as redis
from fastapi import HTTPException

from ..config.settings import config

class RedisCache:
    """Redis cache service for managing application caching."""

    def __init__(self):
        """Initialize Redis cache connection."""
        self._redis: Optional[redis.Redis] = None
        self._url = config.storage_settings["redis_url"]

    async def connect(self) -> None:
        """Connect to Redis server."""
        try:
            self._redis = redis.from_url(self._url)
            await self._redis.ping()
        except redis.ConnectionError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Could not connect to Redis: {str(e)}"
            )

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if exists, None otherwise
        """
        if not self._redis:
            await self.connect()
        
        try:
            value = await self._redis.get(key)
            return json.loads(value) if value else None
        except (redis.RedisError, json.JSONDecodeError) as e:
            raise HTTPException(
                status_code=500,
                detail=f"Cache error: {str(e)}"
            )

    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            expire: Expiration time in seconds or timedelta
            
        Returns:
            bool: True if successful
        """
        if not self._redis:
            await self.connect()
        
        try:
            serialized = json.dumps(value)
            return await self._redis.set(key, serialized, ex=expire)
        except (redis.RedisError, TypeError) as e:
            raise HTTPException(
                status_code=500,
                detail=f"Cache error: {str(e)}"
            )

    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if key was deleted
        """
        if not self._redis:
            await self.connect()
        
        try:
            return bool(await self._redis.delete(key))
        except redis.RedisError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Cache error: {str(e)}"
            )

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if key exists
        """
        if not self._redis:
            await self.connect()
        
        try:
            return bool(await self._redis.exists(key))
        except redis.RedisError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Cache error: {str(e)}"
            )

    async def clear(self) -> bool:
        """
        Clear all cache data.
        
        Returns:
            bool: True if successful
        """
        if not self._redis:
            await self.connect()
        
        try:
            return bool(await self._redis.flushdb())
        except redis.RedisError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Cache error: {str(e)}"
            )

# Global cache instance
cache = RedisCache() 