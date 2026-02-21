"""
Smart Caching Layer

Caches expensive operations to improve performance:
- LLM responses (for identical inputs)
- File system scans (with TTL)
- Context building (until context changes)
- Dependency analysis results
"""

import time
import json
import hashlib
import logging
from typing import Any, Callable, Optional, Dict
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta


@dataclass
class CacheEntry:
    """Single cache entry with metadata"""
    key: str
    value: Any
    created_at: float
    ttl_seconds: Optional[int]
    hit_count: int = 0
    last_hit: Optional[float] = None
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        if self.ttl_seconds is None:
            return False
        return (time.time() - self.created_at) > self.ttl_seconds
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "key": self.key,
            "value": self.value,
            "created_at": self.created_at,
            "ttl_seconds": self.ttl_seconds,
            "hit_count": self.hit_count,
            "last_hit": self.last_hit
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'CacheEntry':
        """Create from dictionary"""
        return CacheEntry(**data)


class SmartCache:
    """
    In-memory cache with TTL and persistence
    
    Features:
    - Time-to-live (TTL) support
    - Automatic expiration
    - Hit/miss statistics
    - Optional disk persistence
    - Memory limits
    """
    
    def __init__(
        self,
        max_entries: int = 1000,
        default_ttl: int = 300,  # 5 minutes
        persist_path: Optional[str] = None
    ):
        self.cache: Dict[str, CacheEntry] = {}
        self.max_entries = max_entries
        self.default_ttl = default_ttl
        self.persist_path = persist_path
        self.logger = logging.getLogger(__name__)
        
        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "expirations": 0
        }
        
        # Load from disk if available
        if persist_path:
            self._load_from_disk()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if miss/expired
        """
        entry = self.cache.get(key)
        
        if entry is None:
            self.stats["misses"] += 1
            return None
        
        # Check expiration
        if entry.is_expired():
            self.logger.debug(f"Cache entry expired: {key}")
            del self.cache[key]
            self.stats["expirations"] += 1
            self.stats["misses"] += 1
            return None
        
        # Update hit stats
        entry.hit_count += 1
        entry.last_hit = time.time()
        self.stats["hits"] += 1
        
        return entry.value
    
    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None
    ) -> None:
        """
        Set cache value
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live (None = use default)
        """
        if ttl_seconds is None:
            ttl_seconds = self.default_ttl
        
        # Enforce max entries
        if len(self.cache) >= self.max_entries:
            self._evict_lru()
        
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=time.time(),
            ttl_seconds=ttl_seconds
        )
        
        self.cache[key] = entry
        
        # Persist if enabled
        if self.persist_path:
            self._persist()
    
    def get_or_compute(
        self,
        key: str,
        compute_fn: Callable[[], Any],
        ttl_seconds: Optional[int] = None
    ) -> Any:
        """
        Get from cache or compute if miss
        
        Args:
            key: Cache key
            compute_fn: Function to compute value on miss
            ttl_seconds: Time to live
        
        Returns:
            Cached or computed value
        """
        value = self.get(key)
        
        if value is not None:
            return value
        
        # Cache miss - compute
        value = compute_fn()
        self.set(key, value, ttl_seconds)
        
        return value
    
    def invalidate(self, key: str) -> bool:
        """
        Invalidate cache entry
        
        Args:
            key: Cache key to invalidate
        
        Returns:
            True if entry existed
        """
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching pattern
        
        Args:
            pattern: Pattern to match (simple substring match)
        
        Returns:
            Number of entries invalidated
        """
        keys_to_remove = [
            key for key in self.cache.keys()
            if pattern in key
        ]
        
        for key in keys_to_remove:
            del self.cache[key]
        
        return len(keys_to_remove)
    
    def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "expirations": 0
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (
            self.stats["hits"] / total_requests
            if total_requests > 0
            else 0.0
        )
        
        return {
            **self.stats,
            "total_entries": len(self.cache),
            "hit_rate": hit_rate,
            "total_requests": total_requests
        }
    
    def _evict_lru(self) -> None:
        """Evict least recently used entry"""
        if not self.cache:
            return
        
        # Find LRU entry
        lru_key = None
        lru_time = float('inf')
        
        for key, entry in self.cache.items():
            last_access = entry.last_hit or entry.created_at
            if last_access < lru_time:
                lru_time = last_access
                lru_key = key
        
        if lru_key:
            del self.cache[lru_key]
            self.stats["evictions"] += 1
            self.logger.debug(f"Evicted LRU entry: {lru_key}")
    
    def _persist(self) -> None:
        """Persist cache to disk"""
        if not self.persist_path:
            return
        
        try:
            Path(self.persist_path).parent.mkdir(parents=True, exist_ok=True)
            
            cache_data = {
                key: entry.to_dict()
                for key, entry in self.cache.items()
            }
            
            with open(self.persist_path, 'w') as f:
                json.dump({
                    "cache": cache_data,
                    "stats": self.stats
                }, f, indent=2)
        
        except Exception as e:
            self.logger.warning(f"Failed to persist cache: {e}")
    
    def _load_from_disk(self) -> None:
        """Load cache from disk"""
        if not self.persist_path or not Path(self.persist_path).exists():
            return
        
        try:
            with open(self.persist_path, 'r') as f:
                data = json.load(f)
            
            # Restore cache entries (skip expired)
            for key, entry_dict in data.get("cache", {}).items():
                entry = CacheEntry.from_dict(entry_dict)
                if not entry.is_expired():
                    self.cache[key] = entry
            
            # Restore stats
            self.stats.update(data.get("stats", {}))
            
            self.logger.info(f"Loaded {len(self.cache)} cache entries from disk")
        
        except Exception as e:
            self.logger.warning(f"Failed to load cache from disk: {e}")


def compute_cache_key(*args, **kwargs) -> str:
    """
    Compute deterministic cache key from arguments
    
    Args:
        *args, **kwargs: Arguments to hash
    
    Returns:
        SHA256 hash as cache key
    """
    # Convert to JSON-serializable format
    key_data = {
        "args": [str(arg) for arg in args],
        "kwargs": {k: str(v) for k, v in sorted(kwargs.items())}
    }
    
    # Compute hash
    key_json = json.dumps(key_data, sort_keys=True)
    return hashlib.sha256(key_json.encode()).hexdigest()[:16]


# Global cache instances
_llm_cache: Optional[SmartCache] = None
_fs_cache: Optional[SmartCache] = None


def get_llm_cache() -> SmartCache:
    """Get singleton LLM cache (longer TTL)"""
    global _llm_cache
    if _llm_cache is None:
        cache_path = Path.home() / ".zenus" / "cache" / "llm_cache.json"
        _llm_cache = SmartCache(
            max_entries=500,
            default_ttl=3600,  # 1 hour for LLM responses
            persist_path=str(cache_path)
        )
    return _llm_cache


def get_fs_cache() -> SmartCache:
    """Get singleton filesystem cache (shorter TTL)"""
    global _fs_cache
    if _fs_cache is None:
        _fs_cache = SmartCache(
            max_entries=1000,
            default_ttl=300,  # 5 minutes for file system
            persist_path=None  # Don't persist FS cache
        )
    return _fs_cache
