"""Tests for Redis cache service."""

import pytest
from datetime import timedelta

from magnetic.services.cache import RedisCache, cache
from magnetic.utils.decorators import cached

@pytest.fixture
async def redis_cache():
    """Create a test Redis cache instance."""
    cache_instance = RedisCache()
    await cache_instance.connect()
    await cache_instance.clear()  # Ensure clean state
    yield cache_instance
    await cache_instance.clear()
    await cache_instance.disconnect()

@pytest.mark.asyncio
async def test_cache_connection(redis_cache):
    """Test Redis connection."""
    assert redis_cache._redis is not None
    await redis_cache.disconnect()
    assert redis_cache._redis is None

@pytest.mark.asyncio
async def test_cache_set_get(redis_cache):
    """Test setting and getting cache values."""
    test_key = "test_key"
    test_value = {"name": "test", "value": 42}
    
    # Test set
    result = await redis_cache.set(test_key, test_value)
    assert result is True
    
    # Test get
    cached_value = await redis_cache.get(test_key)
    assert cached_value == test_value

@pytest.mark.asyncio
async def test_cache_expiration(redis_cache):
    """Test cache expiration."""
    test_key = "expiring_key"
    test_value = "expiring_value"
    
    # Set with 1 second expiration
    await redis_cache.set(test_key, test_value, expire=1)
    
    # Value should exist initially
    assert await redis_cache.exists(test_key)
    
    # Wait for expiration
    import asyncio
    await asyncio.sleep(1.1)
    
    # Value should be gone
    assert not await redis_cache.exists(test_key)

@pytest.mark.asyncio
async def test_cache_delete(redis_cache):
    """Test deleting cache values."""
    test_key = "delete_key"
    test_value = "delete_value"
    
    # Set value
    await redis_cache.set(test_key, test_value)
    assert await redis_cache.exists(test_key)
    
    # Delete value
    result = await redis_cache.delete(test_key)
    assert result is True
    assert not await redis_cache.exists(test_key)

@pytest.mark.asyncio
async def test_cache_clear(redis_cache):
    """Test clearing all cache data."""
    # Set multiple values
    await redis_cache.set("key1", "value1")
    await redis_cache.set("key2", "value2")
    
    # Clear cache
    result = await redis_cache.clear()
    assert result is True
    
    # Verify all values are gone
    assert not await redis_cache.exists("key1")
    assert not await redis_cache.exists("key2")

@pytest.mark.asyncio
async def test_cached_decorator(redis_cache):
    """Test the cached decorator."""
    test_value = {"data": "test"}
    call_count = 0
    
    @cached(expire=timedelta(seconds=30))
    async def test_function(param: str) -> dict:
        nonlocal call_count
        call_count += 1
        return test_value
    
    # First call should execute the function
    result1 = await test_function("test_param")
    assert result1 == test_value
    assert call_count == 1
    
    # Second call should return cached value
    result2 = await test_function("test_param")
    assert result2 == test_value
    assert call_count == 1  # Function not called again
    
    # Different parameter should execute function again
    result3 = await test_function("different_param")
    assert result3 == test_value
    assert call_count == 2 