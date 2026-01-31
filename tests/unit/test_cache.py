"""
Unit tests for the cache manager.
"""

import json
import time
from pathlib import Path

import pytest

from data_loader.cache import CacheEntry, CacheManager


@pytest.mark.unit
class TestCacheEntry:
    """Tests for CacheEntry dataclass."""

    def test_create_entry(self):
        entry = CacheEntry(
            data={"symbol": "AAPL"},
            timestamp=time.time(),
            ttl_days=7,
            provider="fmp",
            key="profile_AAPL",
        )
        assert entry.data == {"symbol": "AAPL"}
        assert entry.provider == "fmp"
        assert entry.key == "profile_AAPL"
        assert entry.ttl_days == 7

    def test_is_expired_false(self):
        entry = CacheEntry(
            data={},
            timestamp=time.time(),
            ttl_days=7,
            provider="fmp",
            key="test",
        )
        assert entry.is_expired is False

    def test_is_expired_true(self):
        # Create entry with timestamp 8 days ago
        old_timestamp = time.time() - (8 * 86400)
        entry = CacheEntry(
            data={},
            timestamp=old_timestamp,
            ttl_days=7,
            provider="fmp",
            key="test",
        )
        assert entry.is_expired is True

    def test_age_seconds(self):
        # Create entry 1 hour ago
        one_hour_ago = time.time() - 3600
        entry = CacheEntry(
            data={},
            timestamp=one_hour_ago,
            ttl_days=7,
            provider="fmp",
            key="test",
        )
        # Allow for some tolerance in timing
        assert 3590 <= entry.age_seconds <= 3610

    def test_age_hours(self):
        # Create entry 2 hours ago
        two_hours_ago = time.time() - (2 * 3600)
        entry = CacheEntry(
            data={},
            timestamp=two_hours_ago,
            ttl_days=7,
            provider="fmp",
            key="test",
        )
        assert 1.9 <= entry.age_hours <= 2.1

    def test_to_dict(self):
        timestamp = time.time()
        entry = CacheEntry(
            data={"value": 123},
            timestamp=timestamp,
            ttl_days=7,
            provider="fmp",
            key="test",
        )
        d = entry.to_dict()
        assert d == {
            "data": {"value": 123},
            "timestamp": timestamp,
            "ttl_days": 7,
            "provider": "fmp",
            "key": "test",
        }

    def test_from_dict(self):
        timestamp = time.time()
        d = {
            "data": {"value": 456},
            "timestamp": timestamp,
            "ttl_days": 14,
            "provider": "polygon",
            "key": "aggs_SPY",
        }
        entry = CacheEntry.from_dict(d)
        assert entry.data == {"value": 456}
        assert entry.timestamp == timestamp
        assert entry.ttl_days == 14
        assert entry.provider == "polygon"
        assert entry.key == "aggs_SPY"

    def test_roundtrip(self):
        original = CacheEntry(
            data={"complex": [1, 2, {"nested": True}]},
            timestamp=time.time(),
            ttl_days=30,
            provider="fred",
            key="CPIAUCSL",
        )
        restored = CacheEntry.from_dict(original.to_dict())
        assert restored.data == original.data
        assert restored.timestamp == original.timestamp
        assert restored.ttl_days == original.ttl_days
        assert restored.provider == original.provider
        assert restored.key == original.key


@pytest.mark.unit
class TestCacheManager:
    """Tests for CacheManager class."""

    def test_init(self, temp_cache_dir):
        cache = CacheManager(base_dir=temp_cache_dir, ttl_days=14)
        assert cache.base_dir == temp_cache_dir
        assert cache.ttl_days == 14
        assert cache.enabled is True

    def test_init_disabled(self, temp_cache_dir):
        cache = CacheManager(base_dir=temp_cache_dir, enabled=False)
        assert cache.enabled is False

    def test_set_and_get(self, temp_cache_dir):
        cache = CacheManager(base_dir=temp_cache_dir)
        data = {"symbol": "AAPL", "price": 185.50}

        success = cache.set("fmp", "profile_AAPL", data)
        assert success is True

        entry = cache.get("fmp", "profile_AAPL")
        assert entry is not None
        assert entry.data == data
        assert entry.provider == "fmp"
        assert entry.key == "profile_AAPL"

    def test_get_nonexistent(self, temp_cache_dir):
        cache = CacheManager(base_dir=temp_cache_dir)
        entry = cache.get("fmp", "nonexistent")
        assert entry is None

    def test_get_expired(self, temp_cache_dir):
        cache = CacheManager(base_dir=temp_cache_dir, ttl_days=1)

        # Manually create an expired entry
        provider_dir = temp_cache_dir / "fmp_cache"
        provider_dir.mkdir(parents=True, exist_ok=True)

        old_entry = {
            "data": {"old": True},
            "timestamp": time.time() - (2 * 86400),  # 2 days ago
            "ttl_days": 1,
            "provider": "fmp",
            "key": "old_key",
        }

        with open(provider_dir / "old_key.json", "w") as f:
            json.dump(old_entry, f)

        # Should return None for expired entry
        entry = cache.get("fmp", "old_key")
        assert entry is None

    def test_get_expired_with_ignore(self, temp_cache_dir):
        cache = CacheManager(base_dir=temp_cache_dir, ttl_days=1)

        # Manually create an expired entry
        provider_dir = temp_cache_dir / "fmp_cache"
        provider_dir.mkdir(parents=True, exist_ok=True)

        old_entry = {
            "data": {"old": True},
            "timestamp": time.time() - (2 * 86400),
            "ttl_days": 1,
            "provider": "fmp",
            "key": "old_key",
        }

        with open(provider_dir / "old_key.json", "w") as f:
            json.dump(old_entry, f)

        # Should return entry when ignoring expiration
        entry = cache.get("fmp", "old_key", ignore_expired=True)
        assert entry is not None
        assert entry.data == {"old": True}

    def test_delete(self, temp_cache_dir):
        cache = CacheManager(base_dir=temp_cache_dir)

        cache.set("fmp", "to_delete", {"data": True})
        assert cache.exists("fmp", "to_delete") is True

        result = cache.delete("fmp", "to_delete")
        assert result is True
        assert cache.exists("fmp", "to_delete") is False

    def test_delete_nonexistent(self, temp_cache_dir):
        cache = CacheManager(base_dir=temp_cache_dir)
        result = cache.delete("fmp", "nonexistent")
        assert result is False

    def test_clear_provider(self, temp_cache_dir):
        cache = CacheManager(base_dir=temp_cache_dir)

        cache.set("fmp", "key1", {"a": 1})
        cache.set("fmp", "key2", {"b": 2})
        cache.set("polygon", "key3", {"c": 3})

        count = cache.clear_provider("fmp")
        assert count == 2

        assert cache.exists("fmp", "key1") is False
        assert cache.exists("fmp", "key2") is False
        assert cache.exists("polygon", "key3") is True

    def test_clear_all(self, temp_cache_dir):
        cache = CacheManager(base_dir=temp_cache_dir)

        cache.set("fmp", "key1", {})
        cache.set("polygon", "key2", {})
        cache.set("fred", "key3", {})

        count = cache.clear_all()
        assert count == 3

        assert cache.exists("fmp", "key1") is False
        assert cache.exists("polygon", "key2") is False
        assert cache.exists("fred", "key3") is False

    def test_clear_expired(self, temp_cache_dir):
        cache = CacheManager(base_dir=temp_cache_dir, ttl_days=1)

        # Create a valid entry
        cache.set("fmp", "valid", {"valid": True})

        # Create an expired entry manually
        provider_dir = temp_cache_dir / "fmp_cache"
        old_entry = {
            "data": {"old": True},
            "timestamp": time.time() - (2 * 86400),
            "ttl_days": 1,
            "provider": "fmp",
            "key": "expired",
        }
        with open(provider_dir / "expired.json", "w") as f:
            json.dump(old_entry, f)

        count = cache.clear_expired()
        assert count == 1

        assert cache.exists("fmp", "valid") is True
        assert cache.exists("fmp", "expired") is False

    def test_exists(self, temp_cache_dir):
        cache = CacheManager(base_dir=temp_cache_dir)

        assert cache.exists("fmp", "test") is False
        cache.set("fmp", "test", {})
        assert cache.exists("fmp", "test") is True

    def test_is_valid(self, temp_cache_dir):
        cache = CacheManager(base_dir=temp_cache_dir, ttl_days=7)

        cache.set("fmp", "test", {})
        assert cache.is_valid("fmp", "test") is True
        assert cache.is_valid("fmp", "nonexistent") is False

    def test_get_stats(self, temp_cache_dir):
        cache = CacheManager(base_dir=temp_cache_dir, ttl_days=7)

        cache.set("fmp", "key1", {"data": "x" * 100})
        cache.set("fmp", "key2", {"data": "y" * 200})
        cache.set("polygon", "key3", {"data": "z" * 50})

        stats = cache.get_stats()

        assert stats["enabled"] is True
        assert stats["ttl_days"] == 7
        assert stats["providers"]["fmp"]["total_entries"] == 2
        assert stats["providers"]["polygon"]["total_entries"] == 1
        assert stats["providers"]["fred"]["total_entries"] == 0

    def test_disabled_cache(self, temp_cache_dir):
        cache = CacheManager(base_dir=temp_cache_dir, enabled=False)

        assert cache.set("fmp", "test", {}) is False
        assert cache.get("fmp", "test") is None
        assert cache.delete("fmp", "test") is False
        assert cache.exists("fmp", "test") is False
        assert cache.is_valid("fmp", "test") is False
        assert cache.clear_provider("fmp") == 0
        assert cache.clear_all() == 0
        assert cache.clear_expired() == 0

    def test_sanitize_key(self, temp_cache_dir):
        cache = CacheManager(base_dir=temp_cache_dir)

        # Key with special characters
        key = "data/path:with*special?chars"
        cache.set("fmp", key, {"test": True})

        # Should be able to retrieve with the same key
        entry = cache.get("fmp", key)
        assert entry is not None
        assert entry.data == {"test": True}

    def test_custom_ttl(self, temp_cache_dir):
        cache = CacheManager(base_dir=temp_cache_dir, ttl_days=7)

        cache.set("fmp", "short_ttl", {"data": True}, ttl_days=1)
        entry = cache.get("fmp", "short_ttl")
        assert entry.ttl_days == 1

        cache.set("fmp", "long_ttl", {"data": True}, ttl_days=30)
        entry = cache.get("fmp", "long_ttl")
        assert entry.ttl_days == 30

    def test_atomic_write(self, temp_cache_dir):
        cache = CacheManager(base_dir=temp_cache_dir)

        # Write data
        cache.set("fmp", "atomic", {"counter": 1})

        # Verify file exists and is valid JSON
        cache_path = temp_cache_dir / "fmp_cache" / "atomic.json"
        assert cache_path.exists()

        with open(cache_path) as f:
            data = json.load(f)
            assert data["data"]["counter"] == 1

    def test_complex_data(self, temp_cache_dir):
        cache = CacheManager(base_dir=temp_cache_dir)

        complex_data = {
            "string": "hello",
            "number": 42,
            "float": 3.14,
            "boolean": True,
            "null": None,
            "list": [1, 2, 3],
            "nested": {
                "a": {"b": {"c": "deep"}},
            },
        }

        cache.set("fmp", "complex", complex_data)
        entry = cache.get("fmp", "complex")

        assert entry.data == complex_data

    def test_unicode_data(self, temp_cache_dir):
        cache = CacheManager(base_dir=temp_cache_dir)

        unicode_data = {
            "company": "日本株式会社",
            "currency": "€",
            "emoji": "📈",
        }

        cache.set("fmp", "unicode", unicode_data)
        entry = cache.get("fmp", "unicode")

        assert entry.data == unicode_data
