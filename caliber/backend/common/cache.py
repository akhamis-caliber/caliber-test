"""
Redis caching utilities for Caliber application
"""

import json
import hashlib
from typing import Any, Optional, Union
import redis
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

class RedisCache:
    """Redis caching utility class"""
    
    def __init__(self):
        self.redis_client = None
        self._connect()
    
    def _connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = redis.from_url(settings.REDIS_URL)
            # Test connection
            self.redis_client.ping()
            logger.info("Redis cache connected successfully")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Caching will be disabled.")
            self.redis_client = None
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a cache key from prefix and arguments"""
        # Create a hash of the arguments for consistent key generation
        key_parts = [prefix]
        
        # Add positional arguments
        for arg in args:
            key_parts.append(str(arg))
        
        # Add keyword arguments (sorted for consistency)
        for key, value in sorted(kwargs.items()):
            key_parts.append(f"{key}:{value}")
        
        # Create hash of the key parts
        key_string = "|".join(key_parts)
        return f"caliber:{hashlib.md5(key_string.encode()).hexdigest()}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.redis_client:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        """Set value in cache with expiration (default 1 hour)"""
        if not self.redis_client:
            return False
        
        try:
            serialized = json.dumps(value, default=str)
            return self.redis_client.setex(key, expire, serialized)
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache delete pattern error: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error: {e}")
            return False
    
    def ttl(self, key: str) -> int:
        """Get time to live for a key"""
        if not self.redis_client:
            return -1
        
        try:
            return self.redis_client.ttl(key)
        except Exception as e:
            logger.error(f"Cache TTL error: {e}")
            return -1

# Global cache instance
cache = RedisCache()

def cache_decorator(prefix: str, expire: int = 3600, key_args: Optional[list] = None):
    """
    Decorator for caching function results
    
    Args:
        prefix: Cache key prefix
        expire: Cache expiration time in seconds
        key_args: List of argument names to include in cache key
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_args:
                # Use specific arguments for cache key
                cache_kwargs = {k: kwargs.get(k) for k in key_args if k in kwargs}
                cache_key = cache._generate_key(prefix, *args, **cache_kwargs)
            else:
                # Use all arguments for cache key
                cache_key = cache._generate_key(prefix, *args, **kwargs)
            
            # Try to get from cache first
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            cache.set(cache_key, result, expire)
            logger.debug(f"Cached result for key: {cache_key}")
            
            return result
        
        return wrapper
    return decorator

def invalidate_cache_pattern(pattern: str):
    """Invalidate cache keys matching pattern"""
    return cache.delete_pattern(pattern)

