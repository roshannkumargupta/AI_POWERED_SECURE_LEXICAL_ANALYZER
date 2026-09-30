"""Thread-safe LRU cache for pure analysis results."""

from __future__ import annotations

import hashlib
import json
import threading
from collections import OrderedDict
from typing import Any

from apsla.models import AnalysisResult


class AnalysisLRUCache:
    """Thread-safe Least-Recently-Used (LRU) cache with fixed capacity.

    Caches pure AnalysisResult instances keyed by SHA-256 hash of:
        (source, language, filename, options_json)
    """

    def __init__(self, capacity: int = 128) -> None:
        self.capacity = capacity
        self._cache: OrderedDict[str, AnalysisResult] = OrderedDict()
        self._lock = threading.Lock()

    @staticmethod
    def compute_key(source: str, language: str, filename: str, options: dict[str, Any]) -> str:
        """Computes deterministic SHA-256 cache key."""
        sorted_opts = json.dumps(options, sort_keys=True)
        raw = f"{source}::{language}::{filename}::{sorted_opts}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, key: str) -> AnalysisResult | None:
        """Retrieves cached AnalysisResult if present, moving entry to MRU position."""
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                return self._cache[key]
            return None

    def put(self, key: str, value: AnalysisResult) -> None:
        """Stores an AnalysisResult in cache, evicting oldest item if capacity is exceeded."""
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = value
            if len(self._cache) > self.capacity:
                self._cache.popitem(last=False)

    def clear(self) -> None:
        """Clears all cached analysis items."""
        with self._lock:
            self._cache.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._cache)

    def size(self) -> int:
        """Return number of cached items."""
        return len(self)


# Global singleton cache instance
ANALYSIS_CACHE = AnalysisLRUCache(capacity=128)
