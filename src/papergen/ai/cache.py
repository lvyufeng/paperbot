"""Response caching for API calls to reduce costs and improve performance.

This module provides a disk-based cache for API responses with TTL (time-to-live)
support. It uses content-based hashing to identify identical requests and stores
responses in JSON format.
"""

import hashlib
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from ..core.logging_config import get_logger


class ResponseCache:
    """Cache for API responses with TTL support.

    Features:
    - Content-based hashing for cache keys
    - TTL (time-to-live) for automatic expiration
    - Disk-based storage for persistence
    - Automatic cleanup of expired entries
    - Statistics tracking (hits, misses, savings)
    """

    def __init__(
        self,
        cache_dir: Path,
        ttl_hours: int = 24,
        max_size_mb: int = 100,
        enabled: bool = True
    ):
        """
        Initialize response cache.

        Args:
            cache_dir: Directory to store cache files
            ttl_hours: Time-to-live in hours (default: 24)
            max_size_mb: Maximum cache size in MB (default: 100)
            enabled: Whether caching is enabled (default: True)
        """
        self.cache_dir = Path(cache_dir)
        self.ttl_seconds = ttl_hours * 3600
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.enabled = enabled
        self.logger = get_logger()

        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "saves": 0,
            "evictions": 0,
            "total_tokens_saved": 0
        }

        # Create cache directory
        if self.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self._load_stats()
            self.logger.info(f"Response cache initialized: {cache_dir} (TTL: {ttl_hours}h)")

    def _generate_cache_key(self, prompt: str, system: str, model: str, temperature: float) -> str:
        """
        Generate cache key from request parameters.

        Args:
            prompt: User prompt
            system: System prompt
            model: Model name
            temperature: Temperature setting

        Returns:
            Cache key (SHA256 hash)
        """
        # Create a deterministic string from parameters
        cache_input = f"{model}|{temperature}|{system}|{prompt}"

        # Generate hash
        hash_obj = hashlib.sha256(cache_input.encode('utf-8'))
        return hash_obj.hexdigest()

    def _get_cache_file(self, cache_key: str) -> Path:
        """Get cache file path for a given key."""
        return self.cache_dir / f"{cache_key}.json"

    def get(
        self,
        prompt: str,
        system: str = "",
        model: str = "",
        temperature: float = 0.7
    ) -> Optional[str]:
        """
        Get cached response if available and not expired.

        Args:
            prompt: User prompt
            system: System prompt
            model: Model name
            temperature: Temperature setting

        Returns:
            Cached response or None if not found/expired
        """
        if not self.enabled:
            return None

        cache_key = self._generate_cache_key(prompt, system, model, temperature)
        cache_file = self._get_cache_file(cache_key)

        if not cache_file.exists():
            self.stats["misses"] += 1
            return None

        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)

            # Check if expired
            cached_time = cache_data.get("timestamp", 0)
            age = time.time() - cached_time

            if age > self.ttl_seconds:
                # Expired - delete file
                cache_file.unlink()
                self.stats["misses"] += 1
                self.logger.debug(f"Cache expired: {cache_key[:8]}... (age: {age/3600:.1f}h)")
                return None

            # Cache hit!
            response = cache_data.get("response")
            tokens_saved = cache_data.get("tokens", 0)

            self.stats["hits"] += 1
            self.stats["total_tokens_saved"] += tokens_saved

            self.logger.info(
                f"Cache HIT: {cache_key[:8]}... "
                f"(age: {age/3600:.1f}h, tokens saved: {tokens_saved})"
            )

            return response

        except Exception as e:
            self.logger.error(f"Error reading cache: {e}")
            self.stats["misses"] += 1
            return None

    def set(
        self,
        prompt: str,
        response: str,
        system: str = "",
        model: str = "",
        temperature: float = 0.7,
        tokens: int = 0
    ) -> None:
        """
        Store response in cache.

        Args:
            prompt: User prompt
            response: API response
            system: System prompt
            model: Model name
            temperature: Temperature setting
            tokens: Token count for statistics
        """
        if not self.enabled:
            return

        cache_key = self._generate_cache_key(prompt, system, model, temperature)
        cache_file = self._get_cache_file(cache_key)

        cache_data = {
            "timestamp": time.time(),
            "response": response,
            "model": model,
            "temperature": temperature,
            "tokens": tokens,
            "prompt_length": len(prompt),
            "response_length": len(response)
        }

        try:
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)

            self.stats["saves"] += 1
            self.logger.debug(f"Cache SAVE: {cache_key[:8]}... (tokens: {tokens})")

            # Check cache size and cleanup if needed
            self._cleanup_if_needed()

        except Exception as e:
            self.logger.error(f"Error writing cache: {e}")

    def _cleanup_if_needed(self) -> None:
        """Clean up cache if it exceeds max size."""
        total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.json"))

        if total_size > self.max_size_bytes:
            self.logger.info(f"Cache size exceeded ({total_size/1024/1024:.1f}MB), cleaning up...")
            self._cleanup_old_entries()

    def _cleanup_old_entries(self, keep_newest: int = 100) -> None:
        """
        Remove old cache entries.

        Args:
            keep_newest: Number of newest entries to keep
        """
        cache_files = list(self.cache_dir.glob("*.json"))

        if len(cache_files) <= keep_newest:
            return

        # Sort by modification time
        cache_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        # Remove old files
        for cache_file in cache_files[keep_newest:]:
            try:
                cache_file.unlink()
                self.stats["evictions"] += 1
            except Exception as e:
                self.logger.error(f"Error deleting cache file: {e}")

        self.logger.info(f"Cleaned up {len(cache_files) - keep_newest} old cache entries")

    def clear(self) -> None:
        """Clear all cache entries."""
        if not self.enabled:
            return

        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
                count += 1
            except Exception as e:
                self.logger.error(f"Error deleting cache file: {e}")

        self.logger.info(f"Cleared {count} cache entries")

        # Reset stats
        self.stats = {
            "hits": 0,
            "misses": 0,
            "saves": 0,
            "evictions": 0,
            "total_tokens_saved": 0
        }
        self._save_stats()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0

        # Calculate cache size
        cache_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.json"))
        cache_count = len(list(self.cache_dir.glob("*.json")))

        return {
            "enabled": self.enabled,
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "saves": self.stats["saves"],
            "evictions": self.stats["evictions"],
            "total_requests": total_requests,
            "hit_rate": f"{hit_rate:.1f}%",
            "tokens_saved": self.stats["total_tokens_saved"],
            "cache_size_mb": f"{cache_size / 1024 / 1024:.2f}",
            "cache_entries": cache_count,
            "ttl_hours": self.ttl_seconds / 3600
        }

    def _load_stats(self) -> None:
        """Load statistics from disk."""
        stats_file = self.cache_dir / "stats.json"
        if stats_file.exists():
            try:
                with open(stats_file, 'r') as f:
                    self.stats = json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading cache stats: {e}")

    def _save_stats(self) -> None:
        """Save statistics to disk."""
        stats_file = self.cache_dir / "stats.json"
        try:
            with open(stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving cache stats: {e}")

    def __del__(self):
        """Save statistics on cleanup."""
        if self.enabled:
            self._save_stats()


class CacheManager:
    """Singleton manager for response cache."""

    _instance: Optional[ResponseCache] = None

    @classmethod
    def get_cache(
        cls,
        cache_dir: Optional[Path] = None,
        ttl_hours: int = 24,
        max_size_mb: int = 100,
        enabled: bool = True
    ) -> ResponseCache:
        """
        Get or create cache instance.

        Args:
            cache_dir: Cache directory (default: .papergen/cache)
            ttl_hours: Time-to-live in hours
            max_size_mb: Maximum cache size in MB
            enabled: Whether caching is enabled

        Returns:
            ResponseCache instance
        """
        if cls._instance is None:
            if cache_dir is None:
                # Default to .papergen/cache in current directory
                cache_dir = Path.cwd() / ".papergen" / "cache"

            cls._instance = ResponseCache(
                cache_dir=cache_dir,
                ttl_hours=ttl_hours,
                max_size_mb=max_size_mb,
                enabled=enabled
            )

        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset cache instance (useful for testing)."""
        cls._instance = None
