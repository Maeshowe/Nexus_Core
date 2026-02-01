"""
OmniData Nexus Core - QoS Semaphore Router

Manages provider-specific concurrency limits using asyncio semaphores.
Ensures API rate limits are respected and resources are fairly distributed.
"""

import asyncio
from dataclasses import dataclass
from typing import Any, Callable, Optional, TypeVar

T = TypeVar('T')


@dataclass
class QoSConfig:
    """Configuration for a provider's QoS settings."""

    max_concurrency: int
    priority: int = 0  # Higher = more priority (not used currently)
    name: str = ""


@dataclass
class QoSStats:
    """Statistics for QoS tracking."""

    total_requests: int = 0
    active_requests: int = 0
    queued_requests: int = 0
    max_concurrent_seen: int = 0


class QoSSemaphoreRouter:
    """
    Routes requests through provider-specific semaphores.

    Ensures each provider's concurrency limit is respected, preventing
    API rate limit violations and ensuring fair resource distribution.

    Default limits:
    - FMP: 3 concurrent requests
    - Polygon: 10 concurrent requests
    - FRED: 1 concurrent request (sequential only)

    Usage:
        router = QoSSemaphoreRouter()

        # Execute with concurrency control
        async with router.acquire("fmp"):
            result = await make_api_call()

        # Or use the execute helper
        result = await router.execute("fmp", make_api_call)
    """

    # Default concurrency limits per provider
    DEFAULT_LIMITS = {
        "fmp": 3,
        "polygon": 10,
        "fred": 1,
    }

    def __init__(
        self,
        limits: Optional[dict[str, int]] = None,
    ):
        """
        Initialize QoS router.

        Args:
            limits: Optional dict of provider -> max_concurrency.
                   Merges with and overrides default limits.
        """
        # Merge provided limits with defaults
        self._limits = {**self.DEFAULT_LIMITS}
        if limits:
            self._limits.update(limits)

        # Create semaphores for each provider
        self._semaphores: dict[str, asyncio.Semaphore] = {}
        for provider, limit in self._limits.items():
            self._semaphores[provider] = asyncio.Semaphore(limit)

        # Track statistics per provider
        self._stats: dict[str, QoSStats] = {
            provider: QoSStats() for provider in self._limits
        }

        # Lock for creating new provider semaphores
        self._lock = asyncio.Lock()

    async def _get_semaphore(self, provider: str) -> asyncio.Semaphore:
        """
        Get or create semaphore for a provider.

        Args:
            provider: Provider name

        Returns:
            asyncio.Semaphore for the provider
        """
        if provider not in self._semaphores:
            async with self._lock:
                # Double-check after acquiring lock
                if provider not in self._semaphores:
                    # Use default limit of 5 for unknown providers
                    limit = self._limits.get(provider, 5)
                    self._semaphores[provider] = asyncio.Semaphore(limit)
                    self._stats[provider] = QoSStats()
                    self._limits[provider] = limit

        return self._semaphores[provider]

    def acquire(self, provider: str) -> "QoSContext":
        """
        Acquire a slot for the specified provider.

        Returns a context manager that holds the semaphore.

        Args:
            provider: Provider name

        Returns:
            QoSContext for use with async with

        Usage:
            async with router.acquire("fmp"):
                result = await make_api_call()
        """
        return QoSContext(self, provider)

    async def execute(
        self,
        provider: str,
        coro_func: Callable[..., Any],
        *args,
        **kwargs,
    ) -> T:
        """
        Execute a coroutine with QoS control.

        Acquires the semaphore, executes the coroutine, then releases.

        Args:
            provider: Provider name
            coro_func: Async function to execute
            *args: Positional arguments for coro_func
            **kwargs: Keyword arguments for coro_func

        Returns:
            Result of coro_func
        """
        async with self.acquire(provider):
            return await coro_func(*args, **kwargs)

    def get_stats(self, provider: Optional[str] = None) -> dict:
        """
        Get QoS statistics.

        Args:
            provider: Optional provider to get stats for

        Returns:
            Dictionary of statistics
        """
        if provider:
            stats = self._stats.get(provider, QoSStats())
            return {
                "provider": provider,
                "max_concurrency": self._limits.get(provider, 0),
                "total_requests": stats.total_requests,
                "active_requests": stats.active_requests,
                "queued_requests": stats.queued_requests,
                "max_concurrent_seen": stats.max_concurrent_seen,
            }

        return {
            p: self.get_stats(p) for p in self._limits
        }

    def get_limit(self, provider: str) -> int:
        """
        Get concurrency limit for a provider.

        Args:
            provider: Provider name

        Returns:
            Max concurrent requests allowed
        """
        return self._limits.get(provider, 5)

    def set_limit(self, provider: str, limit: int) -> None:
        """
        Update concurrency limit for a provider.

        Note: This creates a new semaphore. Existing waiters will
        continue on the old semaphore.

        Args:
            provider: Provider name
            limit: New max concurrency
        """
        if limit < 1:
            raise ValueError("Concurrency limit must be at least 1")

        self._limits[provider] = limit
        self._semaphores[provider] = asyncio.Semaphore(limit)

        if provider not in self._stats:
            self._stats[provider] = QoSStats()

    def get_active_count(self, provider: str) -> int:
        """
        Get number of active requests for a provider.

        Args:
            provider: Provider name

        Returns:
            Number of currently active requests
        """
        stats = self._stats.get(provider, QoSStats())
        return stats.active_requests

    def get_available_slots(self, provider: str) -> int:
        """
        Get number of available slots for a provider.

        Args:
            provider: Provider name

        Returns:
            Number of available concurrent slots
        """
        limit = self._limits.get(provider, 5)
        active = self.get_active_count(provider)
        return max(0, limit - active)

    def is_available(self, provider: str) -> bool:
        """
        Check if a slot is immediately available.

        Args:
            provider: Provider name

        Returns:
            True if a request can start immediately
        """
        return self.get_available_slots(provider) > 0

    async def _on_acquire(self, provider: str) -> None:
        """Called when a slot is acquired."""
        stats = self._stats.get(provider)
        if stats:
            stats.total_requests += 1
            stats.active_requests += 1
            if stats.active_requests > stats.max_concurrent_seen:
                stats.max_concurrent_seen = stats.active_requests

    async def _on_release(self, provider: str) -> None:
        """Called when a slot is released."""
        stats = self._stats.get(provider)
        if stats:
            stats.active_requests = max(0, stats.active_requests - 1)


class QoSContext:
    """
    Context manager for QoS-controlled execution.

    Acquires the provider's semaphore on entry and releases on exit.
    """

    def __init__(self, router: QoSSemaphoreRouter, provider: str):
        self.router = router
        self.provider = provider
        self._semaphore: Optional[asyncio.Semaphore] = None

    async def __aenter__(self) -> "QoSContext":
        self._semaphore = await self.router._get_semaphore(self.provider)
        await self._semaphore.acquire()
        await self.router._on_acquire(self.provider)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.router._on_release(self.provider)
        if self._semaphore:
            self._semaphore.release()


# Convenience: create a global router instance
_default_router: Optional[QoSSemaphoreRouter] = None


def get_default_router() -> QoSSemaphoreRouter:
    """
    Get or create the default QoS router.

    Returns:
        Default QoSSemaphoreRouter instance
    """
    global _default_router
    if _default_router is None:
        _default_router = QoSSemaphoreRouter()
    return _default_router


def reset_default_router() -> None:
    """Reset the default router (mainly for testing)."""
    global _default_router
    _default_router = None
