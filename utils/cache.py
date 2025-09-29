"""
AWS Operations Command Center - Caching Utilities
Simple in-memory caching with TTL support.
"""

import time
import json
import hashlib
from typing import Any, Optional, Callable
from functools import wraps
from config.settings import settings

class SimpleCache:
    """Simple in-memory cache with TTL"""
    
    def __init__(self, default_ttl: int = None):
        self._cache = {}
        self.default_ttl = default_ttl or settings.cache_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key in self._cache:
            value, expiry = self._cache[key]
            if time.time() < expiry:
                return value
            else:
                del self._cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL"""
        ttl = ttl or self.default_ttl
        expiry = time.time() + ttl
        self._cache[key] = (value, expiry)
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        self._cache.clear()
    
    def size(self) -> int:
        """Get number of cached items"""
        return len(self._cache)
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count removed"""
        current_time = time.time()
        expired_keys = [
            key for key, (_, expiry) in self._cache.items()
            if current_time >= expiry
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        return len(expired_keys)

# Global cache instance
cache = SimpleCache()

def cached(ttl: int = None, key_prefix: str = ""):
    """
    Decorator for caching function results
    
    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache keys
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            key_data = {
                'func': func.__name__,
                'args': args,
                'kwargs': kwargs
            }
            key_str = json.dumps(key_data, sort_keys=True, default=str)
            cache_key = f"{key_prefix}{hashlib.md5(key_str.encode()).hexdigest()}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        
        # Add cache control methods to function
        wrapper.cache_clear = lambda: cache.clear()
        wrapper.cache_info = lambda: {'size': cache.size()}
        
        return wrapper
    return decorator

def cache_aws_response(ttl: int = 300):
    """
    Decorator specifically for AWS API responses
    
    Args:
        ttl: Time to live in seconds (default 5 minutes)
    """
    return cached(ttl=ttl, key_prefix="aws_")

def invalidate_cache_pattern(pattern: str) -> int:
    """
    Invalidate cache entries matching a pattern
    
    Args:
        pattern: Pattern to match (simple string contains)
    
    Returns:
        Number of entries invalidated
    """
    keys_to_delete = [
        key for key in cache._cache.keys()
        if pattern in key
    ]
    
    for key in keys_to_delete:
        cache.delete(key)
    
    return len(keys_to_delete)

# Cache statistics
def get_cache_stats() -> dict:
    """Get cache statistics"""
    expired_count = cache.cleanup_expired()
    
    return {
        'size': cache.size(),
        'expired_cleaned': expired_count,
        'default_ttl': cache.default_ttl
    }
