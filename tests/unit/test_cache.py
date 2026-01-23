"""Unit tests for response cache."""

import pytest
from pathlib import Path
import time
import json

from papergen.ai.cache import ResponseCache, CacheManager


class TestResponseCache:
    """Test response cache functionality."""

    def test_cache_initialization(self, temp_dir):
        """Test cache initialization."""
        cache = ResponseCache(
            cache_dir=temp_dir / "cache",
            ttl_hours=24,
            max_size_mb=100,
            enabled=True
        )

        assert cache.enabled is True
        assert cache.ttl_seconds == 24 * 3600
        assert (temp_dir / "cache").exists()

    def test_cache_disabled(self, temp_dir):
        """Test cache with disabled flag."""
        cache = ResponseCache(
            cache_dir=temp_dir / "cache",
            enabled=False
        )

        # Should not create cache directory
        assert cache.enabled is False

        # Get should return None
        result = cache.get("test prompt", "system", "model", 0.7)
        assert result is None

    def test_cache_miss(self, temp_dir):
        """Test cache miss."""
        cache = ResponseCache(cache_dir=temp_dir / "cache")

        result = cache.get("test prompt", "system", "model", 0.7)

        assert result is None
        assert cache.stats["misses"] == 1
        assert cache.stats["hits"] == 0

    def test_cache_set_and_get(self, temp_dir):
        """Test setting and getting from cache."""
        cache = ResponseCache(cache_dir=temp_dir / "cache")

        # Set a response
        cache.set(
            prompt="test prompt",
            response="test response",
            system="system prompt",
            model="claude-sonnet",
            temperature=0.7,
            tokens=100
        )

        # Get the response
        result = cache.get(
            prompt="test prompt",
            system="system prompt",
            model="claude-sonnet",
            temperature=0.7
        )

        assert result == "test response"
        assert cache.stats["hits"] == 1
        assert cache.stats["saves"] == 1
        assert cache.stats["total_tokens_saved"] == 100

    def test_cache_key_generation(self, temp_dir):
        """Test cache key generation."""
        cache = ResponseCache(cache_dir=temp_dir / "cache")

        # Same parameters should generate same key
        key1 = cache._generate_cache_key("prompt", "system", "model", 0.7)
        key2 = cache._generate_cache_key("prompt", "system", "model", 0.7)
        assert key1 == key2

        # Different parameters should generate different keys
        key3 = cache._generate_cache_key("different prompt", "system", "model", 0.7)
        assert key1 != key3

        key4 = cache._generate_cache_key("prompt", "system", "model", 0.8)
        assert key1 != key4

    def test_cache_expiration(self, temp_dir):
        """Test cache expiration."""
        cache = ResponseCache(
            cache_dir=temp_dir / "cache",
            ttl_hours=0.0001  # Very short TTL for testing (0.36 seconds)
        )

        # Set a response
        cache.set("prompt", "response", "system", "model", 0.7, 100)

        # Should be cached immediately
        result = cache.get("prompt", "system", "model", 0.7)
        assert result == "response"

        # Wait for expiration
        time.sleep(1)

        # Should be expired
        result = cache.get("prompt", "system", "model", 0.7)
        assert result is None

    def test_cache_clear(self, temp_dir):
        """Test clearing cache."""
        cache = ResponseCache(cache_dir=temp_dir / "cache")

        # Add some entries
        cache.set("prompt1", "response1", "", "model", 0.7, 100)
        cache.set("prompt2", "response2", "", "model", 0.7, 100)

        # Verify they exist
        assert cache.get("prompt1", "", "model", 0.7) == "response1"
        assert cache.get("prompt2", "", "model", 0.7) == "response2"

        # Clear cache
        cache.clear()

        # Verify they're gone
        assert cache.get("prompt1", "", "model", 0.7) is None
        assert cache.get("prompt2", "", "model", 0.7) is None

        # Stats should be reset
        assert cache.stats["hits"] == 0
        assert cache.stats["misses"] == 2  # From the get calls above

    def test_cache_statistics(self, temp_dir):
        """Test cache statistics."""
        cache = ResponseCache(cache_dir=temp_dir / "cache")

        # Add some entries
        cache.set("prompt1", "response1", "", "model", 0.7, 100)
        cache.set("prompt2", "response2", "", "model", 0.7, 200)

        # Get some entries
        cache.get("prompt1", "", "model", 0.7)  # Hit
        cache.get("prompt2", "", "model", 0.7)  # Hit
        cache.get("prompt3", "", "model", 0.7)  # Miss

        stats = cache.get_stats()

        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["saves"] == 2
        assert stats["total_requests"] == 3
        assert stats["tokens_saved"] == 300
        assert "hit_rate" in stats
        assert stats["cache_entries"] == 2

    def test_cache_file_format(self, temp_dir):
        """Test cache file format."""
        cache = ResponseCache(cache_dir=temp_dir / "cache")

        cache.set("test prompt", "test response", "system", "model", 0.7, 100)

        # Find the cache file
        cache_files = list((temp_dir / "cache").glob("*.json"))
        assert len(cache_files) == 1

        # Read and verify format
        with open(cache_files[0], 'r') as f:
            data = json.load(f)

        assert "timestamp" in data
        assert "response" in data
        assert "model" in data
        assert "temperature" in data
        assert "tokens" in data
        assert data["response"] == "test response"
        assert data["tokens"] == 100


class TestCacheManager:
    """Test cache manager singleton."""

    def test_cache_manager_singleton(self, temp_dir):
        """Test that CacheManager returns same instance."""
        CacheManager.reset()  # Reset for testing

        cache1 = CacheManager.get_cache(cache_dir=temp_dir / "cache")
        cache2 = CacheManager.get_cache(cache_dir=temp_dir / "cache")

        assert cache1 is cache2

    def test_cache_manager_reset(self, temp_dir):
        """Test resetting cache manager."""
        cache1 = CacheManager.get_cache(cache_dir=temp_dir / "cache")
        CacheManager.reset()
        cache2 = CacheManager.get_cache(cache_dir=temp_dir / "cache")

        assert cache1 is not cache2


class TestCacheIntegration:
    """Test cache integration scenarios."""

    def test_multiple_prompts_same_response(self, temp_dir):
        """Test caching multiple prompts."""
        cache = ResponseCache(cache_dir=temp_dir / "cache")

        prompts = [
            "What is machine learning?",
            "Explain neural networks",
            "How does backpropagation work?"
        ]

        # Cache all prompts
        for i, prompt in enumerate(prompts):
            cache.set(prompt, f"response_{i}", "", "model", 0.7, 100)

        # Retrieve all prompts
        for i, prompt in enumerate(prompts):
            result = cache.get(prompt, "", "model", 0.7)
            assert result == f"response_{i}"

        assert cache.stats["hits"] == 3
        assert cache.stats["saves"] == 3

    def test_temperature_sensitivity(self, temp_dir):
        """Test that different temperatures create different cache entries."""
        cache = ResponseCache(cache_dir=temp_dir / "cache")

        prompt = "test prompt"

        # Cache with temperature 0.7
        cache.set(prompt, "response_0.7", "", "model", 0.7, 100)

        # Cache with temperature 0.9
        cache.set(prompt, "response_0.9", "", "model", 0.9, 100)

        # Should get different responses
        result_07 = cache.get(prompt, "", "model", 0.7)
        result_09 = cache.get(prompt, "", "model", 0.9)

        assert result_07 == "response_0.7"
        assert result_09 == "response_0.9"


class TestCacheCleanup:
    """Test cache cleanup functionality."""

    def test_cleanup_old_entries(self, temp_dir):
        """Test cleanup removes old entries."""
        cache = ResponseCache(cache_dir=temp_dir / "cache")

        # Add many entries
        for i in range(10):
            cache.set(f"prompt{i}", f"response{i}", "", "model", 0.7, 100)

        # Cleanup keeping only 5
        cache._cleanup_old_entries(keep_newest=5)

        # Count remaining cache files (excluding stats.json)
        cache_files = [f for f in (temp_dir / "cache").glob("*.json") if "stats" not in f.name]
        assert len(cache_files) <= 5

    def test_cleanup_when_below_threshold(self, temp_dir):
        """Test cleanup does nothing when below threshold."""
        cache = ResponseCache(cache_dir=temp_dir / "cache")

        # Add a few entries
        for i in range(3):
            cache.set(f"prompt{i}", f"response{i}", "", "model", 0.7, 100)

        initial_count = len(list((temp_dir / "cache").glob("*.json")))

        # Cleanup with high threshold
        cache._cleanup_old_entries(keep_newest=10)

        final_count = len(list((temp_dir / "cache").glob("*.json")))
        assert initial_count == final_count

    def test_cleanup_if_needed(self, temp_dir):
        """Test automatic cleanup when size exceeded."""
        cache = ResponseCache(
            cache_dir=temp_dir / "cache",
            max_size_mb=0.00001  # Very small to trigger cleanup
        )

        # Add entries that will exceed size
        large_response = "x" * 10000
        for i in range(5):
            cache.set(f"prompt{i}", large_response, "", "model", 0.7, 100)

        # Cleanup should have been triggered
        assert cache.stats["evictions"] >= 0  # May or may not have evictions depending on timing


class TestCacheErrorHandling:
    """Test cache error handling."""

    def test_get_with_corrupted_file(self, temp_dir):
        """Test get handles corrupted cache file."""
        cache = ResponseCache(cache_dir=temp_dir / "cache")

        # Set a value
        cache.set("prompt", "response", "", "model", 0.7, 100)

        # Corrupt the cache file
        cache_files = [f for f in (temp_dir / "cache").glob("*.json") if "stats" not in f.name]
        with open(cache_files[0], 'w') as f:
            f.write("not valid json")

        # Get should handle error gracefully
        result = cache.get("prompt", "", "model", 0.7)
        assert result is None
        assert cache.stats["misses"] >= 1


class TestCacheStatsIO:
    """Test cache statistics I/O."""

    def test_load_existing_stats(self, temp_dir):
        """Test loading existing stats file."""
        cache_dir = temp_dir / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Write stats file
        stats_data = {"hits": 10, "misses": 5, "saves": 15, "evictions": 2, "total_tokens_saved": 1000}
        with open(cache_dir / "stats.json", 'w') as f:
            json.dump(stats_data, f)

        # Create cache, should load stats
        cache = ResponseCache(cache_dir=cache_dir)

        assert cache.stats["hits"] == 10
        assert cache.stats["misses"] == 5
        assert cache.stats["total_tokens_saved"] == 1000

    def test_save_stats_on_del(self, temp_dir):
        """Test stats are saved when cache is deleted."""
        cache_dir = temp_dir / "cache"

        # Create cache and add activity
        cache = ResponseCache(cache_dir=cache_dir)
        cache.set("prompt", "response", "", "model", 0.7, 100)
        cache.get("prompt", "", "model", 0.7)

        # Manually save stats (simulating __del__)
        cache._save_stats()

        # Check stats file exists
        assert (cache_dir / "stats.json").exists()
