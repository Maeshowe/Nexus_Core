"""
OmniData Nexus Core - Cache Manager

Filesystem-based JSON cache with atomic writes, TTL support,
and provider-specific directories.
"""

import json
import os
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional


@dataclass
class CacheEntry:
    """
    Represents a cached item with metadata.

    Attributes:
        data: The cached data
        timestamp: Unix timestamp when cached
        ttl_days: Time-to-live in days
        provider: Source provider name
        key: Cache key
    """

    data: Any
    timestamp: float
    ttl_days: int
    provider: str
    key: str

    @property
    def expires_at(self) -> datetime:
        """Get expiration datetime."""
        return datetime.fromtimestamp(self.timestamp) + timedelta(days=self.ttl_days)

    @property
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return time.time() > (self.timestamp + (self.ttl_days * 86400))

    @property
    def age_seconds(self) -> float:
        """Get age of entry in seconds."""
        return time.time() - self.timestamp

    @property
    def age_hours(self) -> float:
        """Get age of entry in hours."""
        return self.age_seconds / 3600

    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON storage."""
        return {
            "data": self.data,
            "timestamp": self.timestamp,
            "ttl_days": self.ttl_days,
            "provider": self.provider,
            "key": self.key,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CacheEntry":
        """Deserialize from dictionary."""
        return cls(
            data=d["data"],
            timestamp=d["timestamp"],
            ttl_days=d["ttl_days"],
            provider=d["provider"],
            key=d["key"],
        )


class CacheManager:
    """
    Filesystem-based JSON cache with atomic writes.

    Features:
    - Provider-specific directories (fmp_cache, polygon_cache, fred_cache)
    - Atomic writes using temp file + rename pattern
    - TTL-based expiration
    - Thread-safe file operations

    Usage:
        cache = CacheManager(base_dir=Path("./data/cache"), ttl_days=7)

        # Write to cache
        cache.set("fmp", "profile_AAPL", {"symbol": "AAPL", ...})

        # Read from cache
        entry = cache.get("fmp", "profile_AAPL")
        if entry and not entry.is_expired:
            print(entry.data)

        # Delete from cache
        cache.delete("fmp", "profile_AAPL")
    """

    def __init__(
        self,
        base_dir: Path,
        ttl_days: int = 7,
        enabled: bool = True,
    ):
        """
        Initialize cache manager.

        Args:
            base_dir: Base directory for cache storage
            ttl_days: Default TTL for cache entries
            enabled: Whether caching is enabled
        """
        self.base_dir = Path(base_dir)
        self.ttl_days = ttl_days
        self.enabled = enabled

        # Create base directory if enabled
        if self.enabled:
            self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_provider_dir(self, provider: str) -> Path:
        """Get directory for a specific provider."""
        return self.base_dir / f"{provider}_cache"

    def _get_cache_path(self, provider: str, key: str) -> Path:
        """Get full path for a cache entry."""
        # Sanitize key to be filesystem-safe
        safe_key = self._sanitize_key(key)
        return self._get_provider_dir(provider) / f"{safe_key}.json"

    @staticmethod
    def _sanitize_key(key: str) -> str:
        """
        Sanitize cache key for filesystem safety.

        Replaces unsafe characters with underscores.
        """
        # Replace common unsafe characters
        unsafe_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', ' ']
        result = key
        for char in unsafe_chars:
            result = result.replace(char, '_')
        return result

    def set(
        self,
        provider: str,
        key: str,
        data: Any,
        ttl_days: Optional[int] = None,
    ) -> bool:
        """
        Store data in cache.

        Uses atomic write pattern (temp file + rename) to prevent
        corruption from interrupted writes.

        Args:
            provider: Provider name (fmp, polygon, fred)
            key: Cache key
            data: Data to cache (must be JSON-serializable)
            ttl_days: Optional TTL override

        Returns:
            True if successfully cached, False otherwise
        """
        if not self.enabled:
            return False

        try:
            # Ensure provider directory exists
            provider_dir = self._get_provider_dir(provider)
            provider_dir.mkdir(parents=True, exist_ok=True)

            # Create cache entry
            entry = CacheEntry(
                data=data,
                timestamp=time.time(),
                ttl_days=ttl_days or self.ttl_days,
                provider=provider,
                key=key,
            )

            cache_path = self._get_cache_path(provider, key)

            # Atomic write: write to temp file, then rename
            fd, temp_path = tempfile.mkstemp(
                suffix=".json.tmp",
                dir=provider_dir,
            )

            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    json.dump(entry.to_dict(), f, indent=2, ensure_ascii=False)

                # Atomic rename (on POSIX systems)
                os.replace(temp_path, cache_path)
                return True

            except Exception:
                # Clean up temp file on failure
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                raise

        except Exception:
            return False

    def get(
        self,
        provider: str,
        key: str,
        ignore_expired: bool = False,
    ) -> Optional[CacheEntry]:
        """
        Retrieve data from cache.

        Args:
            provider: Provider name
            key: Cache key
            ignore_expired: If True, return expired entries

        Returns:
            CacheEntry if found and valid, None otherwise
        """
        if not self.enabled:
            return None

        cache_path = self._get_cache_path(provider, key)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, encoding='utf-8') as f:
                data = json.load(f)

            entry = CacheEntry.from_dict(data)

            # Check expiration
            if entry.is_expired and not ignore_expired:
                return None

            return entry

        except (OSError, json.JSONDecodeError, KeyError):
            # Invalid or corrupted cache file
            return None

    def delete(self, provider: str, key: str) -> bool:
        """
        Delete a cache entry.

        Args:
            provider: Provider name
            key: Cache key

        Returns:
            True if deleted, False if not found or error
        """
        if not self.enabled:
            return False

        cache_path = self._get_cache_path(provider, key)

        try:
            if cache_path.exists():
                cache_path.unlink()
                return True
            return False
        except OSError:
            return False

    def clear_provider(self, provider: str) -> int:
        """
        Clear all cache entries for a provider.

        Args:
            provider: Provider name

        Returns:
            Number of entries deleted
        """
        if not self.enabled:
            return 0

        provider_dir = self._get_provider_dir(provider)

        if not provider_dir.exists():
            return 0

        count = 0
        for cache_file in provider_dir.glob("*.json"):
            try:
                cache_file.unlink()
                count += 1
            except OSError:
                pass

        return count

    def clear_all(self) -> int:
        """
        Clear all cache entries for all providers.

        Returns:
            Total number of entries deleted
        """
        if not self.enabled:
            return 0

        total = 0
        for provider in ["fmp", "polygon", "fred"]:
            total += self.clear_provider(provider)

        return total

    def clear_expired(self, provider: Optional[str] = None) -> int:
        """
        Delete expired cache entries.

        Args:
            provider: Optional provider to limit cleanup

        Returns:
            Number of expired entries deleted
        """
        if not self.enabled:
            return 0

        providers = [provider] if provider else ["fmp", "polygon", "fred"]
        count = 0

        for prov in providers:
            provider_dir = self._get_provider_dir(prov)

            if not provider_dir.exists():
                continue

            for cache_file in provider_dir.glob("*.json"):
                try:
                    with open(cache_file, encoding='utf-8') as f:
                        data = json.load(f)

                    entry = CacheEntry.from_dict(data)

                    if entry.is_expired:
                        cache_file.unlink()
                        count += 1

                except (OSError, json.JSONDecodeError, KeyError):
                    # Remove corrupted files
                    try:
                        cache_file.unlink()
                        count += 1
                    except OSError:
                        pass

        return count

    def get_stats(self, provider: Optional[str] = None) -> dict:
        """
        Get cache statistics.

        Args:
            provider: Optional provider to limit stats

        Returns:
            Dictionary with cache statistics
        """
        if not self.enabled:
            return {"enabled": False}

        providers = [provider] if provider else ["fmp", "polygon", "fred"]
        stats = {
            "enabled": True,
            "base_dir": str(self.base_dir),
            "ttl_days": self.ttl_days,
            "providers": {},
        }

        for prov in providers:
            provider_dir = self._get_provider_dir(prov)

            prov_stats = {
                "total_entries": 0,
                "expired_entries": 0,
                "valid_entries": 0,
                "total_size_bytes": 0,
            }

            if provider_dir.exists():
                for cache_file in provider_dir.glob("*.json"):
                    prov_stats["total_entries"] += 1
                    prov_stats["total_size_bytes"] += cache_file.stat().st_size

                    try:
                        with open(cache_file, encoding='utf-8') as f:
                            data = json.load(f)
                        entry = CacheEntry.from_dict(data)

                        if entry.is_expired:
                            prov_stats["expired_entries"] += 1
                        else:
                            prov_stats["valid_entries"] += 1

                    except (OSError, json.JSONDecodeError, KeyError):
                        prov_stats["expired_entries"] += 1

            stats["providers"][prov] = prov_stats

        return stats

    def exists(self, provider: str, key: str) -> bool:
        """
        Check if a cache entry exists (ignoring expiration).

        Args:
            provider: Provider name
            key: Cache key

        Returns:
            True if entry exists
        """
        if not self.enabled:
            return False

        return self._get_cache_path(provider, key).exists()

    def is_valid(self, provider: str, key: str) -> bool:
        """
        Check if a valid (non-expired) cache entry exists.

        Args:
            provider: Provider name
            key: Cache key

        Returns:
            True if valid entry exists
        """
        entry = self.get(provider, key)
        return entry is not None and not entry.is_expired
