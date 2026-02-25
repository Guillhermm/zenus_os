"""
Intent Memoization Cache

Caches Intent IR translations to avoid redundant LLM calls:
- Hash user input + context
- Cache Intent IR for 1 hour
- 2-3x faster for repeated commands
- Zero token cost for cache hits
"""

import hashlib
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict

from zenus_core.brain.llm.schemas import IntentIR


@dataclass
class CachedIntent:
    """Cached intent with metadata"""
    intent_data: Dict[str, Any]  # IntentIR as dict
    user_input: str
    context_hash: str
    created_at: float
    hit_count: int = 0
    last_hit: Optional[float] = None
    
    def is_expired(self, ttl_seconds: int = 3600) -> bool:
        """Check if cache entry expired (default 1 hour)"""
        return (time.time() - self.created_at) > ttl_seconds
    
    def to_dict(self) -> Dict:
        """Convert to dict for JSON"""
        return {
            'intent_data': self.intent_data,
            'user_input': self.user_input,
            'context_hash': self.context_hash,
            'created_at': self.created_at,
            'hit_count': self.hit_count,
            'last_hit': self.last_hit,
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'CachedIntent':
        """Create from dict"""
        return CachedIntent(**data)


class IntentCache:
    """
    Intent memoization cache
    
    Caches IntentIR objects keyed by (user_input + context) hash.
    Dramatically reduces token usage for repeated commands.
    
    Example:
        "list files" in ~/projects
        → Cache hit → Zero tokens, instant response
    """
    
    def __init__(
        self,
        cache_path: Optional[str] = None,
        ttl_seconds: int = 3600,  # 1 hour default
        max_entries: int = 500,
    ):
        if cache_path is None:
            cache_path = Path.home() / ".zenus" / "cache" / "intent_cache.json"
        
        self.cache_path = Path(cache_path)
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        
        # In-memory cache
        self.cache: Dict[str, CachedIntent] = {}
        
        # Stats
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expirations': 0,
            'tokens_saved': 0,  # Estimated
        }
        
        # Load from disk
        self._load()
    
    def get(
        self,
        user_input: str,
        context: str = ""
    ) -> Optional[IntentIR]:
        """
        Get cached intent
        
        Args:
            user_input: User's command
            context: Contextual information
        
        Returns:
            Cached IntentIR or None if miss/expired
        """
        cache_key = self._compute_key(user_input, context)
        
        entry = self.cache.get(cache_key)
        if entry is None:
            self.stats['misses'] += 1
            return None
        
        # Check expiration
        if entry.is_expired(self.ttl_seconds):
            del self.cache[cache_key]
            self.stats['expirations'] += 1
            self.stats['misses'] += 1
            self._save()
            return None
        
        # Update hit stats
        entry.hit_count += 1
        entry.last_hit = time.time()
        self.stats['hits'] += 1
        
        # Estimate tokens saved (rough)
        # Typical translation: ~1000 input + 200 output tokens
        self.stats['tokens_saved'] += 1200
        
        self._save()
        
        # Reconstruct IntentIR from cached data
        try:
            return IntentIR.model_validate(entry.intent_data)
        except Exception as e:
            # Cache corrupted, remove entry
            del self.cache[cache_key]
            self.stats['misses'] += 1
            return None
    
    def set(
        self,
        user_input: str,
        context: str,
        intent: IntentIR
    ):
        """
        Cache an intent
        
        Args:
            user_input: User's command
            context: Contextual information
            intent: IntentIR to cache
        """
        cache_key = self._compute_key(user_input, context)
        
        # Enforce max entries (LRU eviction)
        if len(self.cache) >= self.max_entries:
            self._evict_lru()
        
        # Convert IntentIR to dict
        intent_data = intent.model_dump()
        
        # Create cache entry
        entry = CachedIntent(
            intent_data=intent_data,
            user_input=user_input[:200],  # Truncate for storage
            context_hash=hashlib.sha256(context.encode()).hexdigest()[:16],
            created_at=time.time(),
        )
        
        self.cache[cache_key] = entry
        self._save()
    
    def invalidate(self, user_input: str, context: str = "") -> bool:
        """
        Invalidate specific cache entry
        
        Args:
            user_input: User's command
            context: Contextual information
        
        Returns:
            True if entry existed
        """
        cache_key = self._compute_key(user_input, context)
        
        if cache_key in self.cache:
            del self.cache[cache_key]
            self._save()
            return True
        
        return False
    
    def clear(self):
        """Clear all cache entries"""
        self.cache.clear()
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expirations': 0,
            'tokens_saved': 0,
        }
        self._save()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (
            self.stats['hits'] / total_requests
            if total_requests > 0
            else 0.0
        )
        
        # Estimate cost saved (rough: $3 per 1M tokens for Claude)
        estimated_cost_saved = (self.stats['tokens_saved'] / 1_000_000) * 3.0
        
        return {
            **self.stats,
            'total_entries': len(self.cache),
            'hit_rate': hit_rate,
            'total_requests': total_requests,
            'estimated_cost_saved': estimated_cost_saved,
        }
    
    def _compute_key(self, user_input: str, context: str) -> str:
        """Compute cache key from input + context"""
        # Normalize
        normalized_input = user_input.lower().strip()
        
        # Combine input + context
        combined = f"{normalized_input}|{context}"
        
        # Hash for compact key
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def _evict_lru(self):
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
            self.stats['evictions'] += 1
    
    def _load(self):
        """Load cache from disk"""
        if not self.cache_path.exists():
            return
        
        try:
            with open(self.cache_path, 'r') as f:
                data = json.load(f)
            
            # Restore cache entries (skip expired)
            for key, entry_dict in data.get('cache', {}).items():
                entry = CachedIntent.from_dict(entry_dict)
                if not entry.is_expired(self.ttl_seconds):
                    self.cache[key] = entry
            
            # Restore stats
            if 'stats' in data:
                self.stats.update(data['stats'])
        
        except Exception as e:
            # Corrupted cache, start fresh
            pass
    
    def _save(self):
        """Save cache to disk"""
        try:
            data = {
                'cache': {
                    key: entry.to_dict()
                    for key, entry in self.cache.items()
                },
                'stats': self.stats,
            }
            
            with open(self.cache_path, 'w') as f:
                json.dump(data, f, indent=2)
        
        except Exception as e:
            # Non-critical, just skip
            pass


# Global cache instance
_intent_cache: Optional[IntentCache] = None


def get_intent_cache() -> IntentCache:
    """Get singleton intent cache"""
    global _intent_cache
    if _intent_cache is None:
        _intent_cache = IntentCache()
    return _intent_cache
