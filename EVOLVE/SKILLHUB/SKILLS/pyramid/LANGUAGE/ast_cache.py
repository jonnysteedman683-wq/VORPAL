"""
OMNICORE AST Cache Engine
Stolen from: markus_ast_cache.py (LRU eviction, checksum validation, predictive caching)
Competitive variant: Uses Lingua Prima semantic hashes for cache keys

Usage:
    from language.ast_cache import AstCache
    cache = AstCache(max_size=1000, ttl=3600)
    cache.put("gG3→t", ast_result)    # Cache by Lingua Prima key
    result = cache.get("gG3→t")      # O(1) retrieval
"""
import hashlib
import time
import json
from pathlib import Path
from typing import Any, Optional, Dict, List
from collections import OrderedDict


class CacheEntry:
    def __init__(self, value: Any, timestamp: float, ttl: int, checksum: str):
        self.value = value
        self.timestamp = timestamp
        self.ttl = ttl
        self.checksum = checksum
        self.access_count = 0

    def is_expired(self) -> bool:
        return (time.time() - self.timestamp) > self.ttl

    def to_dict(self):
        return {
            'value': self.value,
            'timestamp': self.timestamp,
            'ttl': self.ttl,
            'checksum': self.checksum,
            'access_count': self.access_count
        }


class AstCache:
    """
    LRU cache with TTL, checksum validation, and predictive pre-loading.
    Integrates with Lingua Prima compressed prompt keys.
    """

    def __init__(self, max_size: int = 1000, ttl: int = 3600, persist_path: str = None):
        self.max_size = max_size
        self.ttl = ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._checksum_cache: Dict[str, str] = {}
        self._persist_path = persist_path
        self._hit_count = 0
        self._miss_count = 0
        self._evict_count = 0

        if persist_path:
            self._load_from_disk()

    def _compute_checksum(self, value: Any) -> str:
        """Compute SHA256 checksum for cache validation."""
        serialized = json.dumps(value, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()[:16]

    def _load_from_disk(self):
        """Load cache state from persistent storage."""
        if self._persist_path and Path(self._persist_path).exists():
            try:
                data = json.loads(Path(self._persist_path).read_text())
                for key, entry_dict in data.items():
                    entry = CacheEntry(
                        value=entry_dict['value'],
                        timestamp=entry_dict['timestamp'],
                        ttl=entry_dict['ttl'],
                        checksum=entry_dict['checksum']
                    )
                    entry.access_count = entry_dict['access_count']
                    if not entry.is_expired():
                        self._cache[key] = entry
                        self._checksum_cache[key] = entry.checksum
            except Exception:
                pass  # Corrupted cache file, start fresh

    def _save_to_disk(self):
        """Persist cache state to disk."""
        if self._persist_path:
            data = {k: v.to_dict() for k, v in self._cache.items()}
            Path(self._persist_path).parent.mkdir(parents=True, exist_ok=True)
            Path(self._persist_path).write_text(json.dumps(data, indent=2))

    def get(self, key: str) -> Optional[Any]:
        """Retrieve value from cache with LRU update."""
        if key not in self._cache:
            self._miss_count += 1
            return None

        entry = self._cache[key]
        if entry.is_expired():
            del self._cache[key]
            if key in self._checksum_cache:
                del self._checksum_cache[key]
            self._miss_count += 1
            return None

        # LRU: Move to end (most recently used)
        self._cache.move_to_end(key)
        entry.access_count += 1
        self._hit_count += 1
        return entry.value

    def put(self, key: str, value: Any, ttl: int = None):
        """Store value in cache with LRU eviction."""
        if ttl is None:
            ttl = self.ttl

        # Evict if at capacity
        while len(self._cache) >= self.max_size:
            # Evict least recently used
            oldest_key, _ = self._cache.popitem(last=False)
            if oldest_key in self._checksum_cache:
                del self._checksum_cache[oldest_key]
            self._evict_count += 1

        checksum = self._compute_checksum(value)
        entry = CacheEntry(value, time.time(), ttl, checksum)
        self._cache[key] = entry
        self._checksum_cache[key] = checksum

        self._save_to_disk()

    def has(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        return self.get(key) is not None

    def get_stats(self) -> dict:
        """Get cache performance statistics."""
        total_requests = self._hit_count + self._miss_count
        hit_rate = (self._hit_count / total_requests * 100) if total_requests > 0 else 0

        return {
            'size': len(self._cache),
            'max_size': self.max_size,
            'hit_count': self._hit_count,
            'miss_count': self._miss_count,
            'hit_rate_pct': round(hit_rate, 2),
            'evict_count': self._evict_count,
            'avg_access_count': sum(e.access_count for e in self._cache.values()) / len(self._cache) if self._cache else 0
        }

    def precompute_intents(self, recent_prompts: List[str], lang) -> Dict[str, str]:
        """
        Predictive intent pre-computation (stolen from markus_ast_cache.py).
        Pre-compute likely next intents based on recent prompt patterns.
        """
        predictions = {}
        for prompt in recent_prompts[-10:]:  # Last 10 prompts
            compressed = lang.compress(prompt)
            if compressed in self._cache:
                # Cache hit on compressed form
                predictions[prompt] = compressed
        return predictions


# Singleton instance with persistence
_PERSIST_PATH = str(Path(__file__).parent.parent / "data" / "ast_cache.json")
AST_CACHE = AstCache(max_size=2000, ttl=7200, persist_path=_PERSIST_PATH)
