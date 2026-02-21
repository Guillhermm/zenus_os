"""
Tests for smart caching layer
"""

import time
import pytest
from zenus_core.execution.smart_cache import SmartCache, compute_cache_key


def test_cache_initialization():
    """Test cache initialization"""
    cache = SmartCache(max_entries=100, default_ttl=60)
    assert cache.max_entries == 100
    assert cache.default_ttl == 60
    assert len(cache.cache) == 0


def test_cache_set_and_get():
    """Test basic set/get operations"""
    cache = SmartCache()
    
    cache.set("key1", "value1")
    result = cache.get("key1")
    
    assert result == "value1"
    assert cache.stats["hits"] == 1
    assert cache.stats["misses"] == 0


def test_cache_miss():
    """Test cache miss"""
    cache = SmartCache()
    
    result = cache.get("nonexistent")
    
    assert result is None
    assert cache.stats["misses"] == 1
    assert cache.stats["hits"] == 0


def test_cache_ttl_expiration():
    """Test TTL expiration"""
    cache = SmartCache(default_ttl=1)  # 1 second TTL
    
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"
    
    # Wait for expiration
    time.sleep(1.1)
    
    result = cache.get("key1")
    assert result is None
    assert cache.stats["expirations"] == 1


def test_get_or_compute():
    """Test get_or_compute pattern"""
    cache = SmartCache()
    
    call_count = [0]
    
    def expensive_computation():
        call_count[0] += 1
        return "computed_value"
    
    # First call - should compute
    result1 = cache.get_or_compute("key1", expensive_computation)
    assert result1 == "computed_value"
    assert call_count[0] == 1
    
    # Second call - should use cache
    result2 = cache.get_or_compute("key1", expensive_computation)
    assert result2 == "computed_value"
    assert call_count[0] == 1  # Not called again
    
    # Stats check
    assert cache.stats["hits"] == 1
    assert cache.stats["misses"] == 1


def test_cache_invalidation():
    """Test cache invalidation"""
    cache = SmartCache()
    
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"
    
    # Invalidate
    result = cache.invalidate("key1")
    assert result is True
    
    # Should be gone
    assert cache.get("key1") is None


def test_cache_invalidate_pattern():
    """Test pattern-based invalidation"""
    cache = SmartCache()
    
    cache.set("user:1:name", "Alice")
    cache.set("user:1:email", "alice@example.com")
    cache.set("user:2:name", "Bob")
    
    # Invalidate all user:1 entries
    count = cache.invalidate_pattern("user:1")
    assert count == 2
    
    # user:1 entries should be gone
    assert cache.get("user:1:name") is None
    assert cache.get("user:1:email") is None
    
    # user:2 should still exist
    assert cache.get("user:2:name") == "Bob"


def test_cache_clear():
    """Test cache clear"""
    cache = SmartCache()
    
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    
    cache.clear()
    
    assert len(cache.cache) == 0
    assert cache.stats["hits"] == 0
    assert cache.stats["misses"] == 0


def test_cache_lru_eviction():
    """Test LRU eviction when max entries reached"""
    cache = SmartCache(max_entries=3)
    
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.set("key3", "value3")
    
    # Access key1 to make it more recent
    cache.get("key1")
    
    # Add key4 - should evict key2 (least recently used)
    cache.set("key4", "value4")
    
    assert cache.get("key2") is None
    assert cache.get("key1") == "value1"
    assert cache.get("key4") == "value4"
    assert cache.stats["evictions"] == 1


def test_compute_cache_key():
    """Test cache key computation"""
    key1 = compute_cache_key("arg1", "arg2", kwarg1="value1")
    key2 = compute_cache_key("arg1", "arg2", kwarg1="value1")
    key3 = compute_cache_key("arg1", "different", kwarg1="value1")
    
    # Same args should produce same key
    assert key1 == key2
    
    # Different args should produce different key
    assert key1 != key3
    
    # Keys should be reasonable length
    assert len(key1) == 16  # We use [:16] truncation


def test_cache_hit_rate():
    """Test hit rate calculation"""
    cache = SmartCache()
    
    cache.set("key1", "value1")
    
    # 3 hits, 2 misses
    cache.get("key1")  # hit
    cache.get("key1")  # hit
    cache.get("key1")  # hit
    cache.get("key2")  # miss
    cache.get("key3")  # miss
    
    stats = cache.get_stats()
    
    assert stats["hits"] == 3
    assert stats["misses"] == 2
    assert stats["total_requests"] == 5
    assert stats["hit_rate"] == 0.6
