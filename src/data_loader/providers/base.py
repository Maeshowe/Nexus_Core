"""
OmniData Nexus Core - Base Data Provider

Abstract base class for all data providers (FMP, Polygon, FRED).
Defines the interface for fetching, normalizing, and caching data.
"""

import hashlib
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

import aiohttp

from ..cache import CacheManager
from ..config import ProviderConfig
from ..health import HealthMonitor
from ..http_client import HttpClient, HttpError, HttpResponse, RateLimitError


@dataclass
class ProviderResponse:
    """
    Standardized response from a data provider.

    Attributes:
        success: Whether the request succeeded
        data: The response data (normalized)
        provider: Provider name
        endpoint: API endpoint called
        from_cache: Whether data was served from cache
        latency_ms: Request latency in milliseconds
        error: Error message if failed
        raw_response: Original response (for debugging)
    """

    success: bool
    data: Any
    provider: str
    endpoint: str
    from_cache: bool = False
    latency_ms: float = 0.0
    error: Optional[str] = None
    raw_response: Optional[Any] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "data": self.data,
            "provider": self.provider,
            "endpoint": self.endpoint,
            "from_cache": self.from_cache,
            "latency_ms": round(self.latency_ms, 2),
            "error": self.error,
        }


class BaseDataProvider(ABC):
    """
    Abstract base class for data providers.

    All providers (FMP, Polygon, FRED) inherit from this class and implement:
    - fetch(): Async data fetching from the API
    - normalize(): Response normalization to consistent format
    - cache_key(): Cache key generation

    Features:
    - Automatic caching with TTL
    - Health monitoring integration
    - Standardized response format
    - Error handling

    Usage:
        class FMPProvider(BaseDataProvider):
            @property
            def provider_name(self) -> str:
                return "fmp"

            async def fetch(self, session, endpoint, **params):
                # Implementation
                pass

            def normalize(self, data, endpoint):
                # Implementation
                pass

            def cache_key(self, endpoint, **params):
                # Implementation
                pass
    """

    def __init__(
        self,
        config: ProviderConfig,
        http_client: HttpClient,
        cache: CacheManager,
        health_monitor: HealthMonitor,
    ):
        """
        Initialize base provider.

        Args:
            config: Provider-specific configuration
            http_client: HTTP client for API requests
            cache: Cache manager for caching responses
            health_monitor: Health monitor for tracking metrics
        """
        self.config = config
        self.http_client = http_client
        self.cache = cache
        self.health_monitor = health_monitor

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get the provider name (fmp, polygon, fred)."""
        pass

    @property
    def base_url(self) -> str:
        """Get the base URL for API requests."""
        return self.config.base_url

    @property
    def api_key(self) -> str:
        """Get the API key."""
        return self.config.api_key

    @abstractmethod
    async def fetch(
        self,
        session: aiohttp.ClientSession,
        endpoint: str,
        **params,
    ) -> HttpResponse:
        """
        Fetch data from the API.

        Args:
            session: aiohttp ClientSession
            endpoint: API endpoint to call
            **params: Endpoint-specific parameters

        Returns:
            HttpResponse with raw API response

        Raises:
            HttpError: For HTTP-related errors
        """
        pass

    @abstractmethod
    def normalize(self, data: Any, endpoint: str) -> Any:
        """
        Normalize API response to consistent format.

        Args:
            data: Raw API response data
            endpoint: Endpoint that was called

        Returns:
            Normalized data structure
        """
        pass

    @abstractmethod
    def cache_key(self, endpoint: str, **params) -> str:
        """
        Generate cache key for a request.

        Args:
            endpoint: API endpoint
            **params: Request parameters

        Returns:
            Unique cache key string
        """
        pass

    def _generate_cache_key(self, prefix: str, **params) -> str:
        """
        Generate a cache key from prefix and parameters.

        Helper method for subclasses to generate consistent cache keys.

        Args:
            prefix: Key prefix (usually endpoint name)
            **params: Parameters to include in key

        Returns:
            Cache key string
        """
        # Sort params for consistent ordering
        sorted_params = sorted(params.items())
        param_str = "_".join(f"{k}={v}" for k, v in sorted_params if v is not None)

        key = f"{prefix}_{param_str}" if param_str else prefix

        # Hash if too long
        if len(key) > 200:
            hash_val = hashlib.md5(key.encode()).hexdigest()[:16]
            key = f"{prefix}_{hash_val}"

        return key

    async def get(
        self,
        session: aiohttp.ClientSession,
        endpoint: str,
        use_cache: bool = True,
        **params,
    ) -> ProviderResponse:
        """
        Get data from provider with caching and health tracking.

        This is the main entry point for fetching data. It handles:
        1. Cache lookup (if enabled)
        2. API fetch (if not cached or cache disabled)
        3. Response normalization
        4. Cache storage
        5. Health metric recording

        Args:
            session: aiohttp ClientSession
            endpoint: API endpoint to call
            use_cache: Whether to use caching
            **params: Endpoint-specific parameters

        Returns:
            ProviderResponse with data or error
        """
        start_time = time.perf_counter()
        cache_key = self.cache_key(endpoint, **params)

        # Try cache first
        if use_cache:
            cached = self.cache.get(self.provider_name, cache_key)
            if cached and not cached.is_expired:
                return ProviderResponse(
                    success=True,
                    data=cached.data,
                    provider=self.provider_name,
                    endpoint=endpoint,
                    from_cache=True,
                    latency_ms=0.0,
                )

        # Fetch from API
        try:
            response = await self.fetch(session, endpoint, **params)
            elapsed_ms = (time.perf_counter() - start_time) * 1000

            # Normalize response
            normalized_data = self.normalize(response.data, endpoint)

            # Cache the result
            if use_cache:
                self.cache.set(self.provider_name, cache_key, normalized_data)

            # Record success
            self.health_monitor.record_success(
                provider=self.provider_name,
                endpoint=endpoint,
                latency_ms=elapsed_ms,
                status_code=response.status,
            )

            return ProviderResponse(
                success=True,
                data=normalized_data,
                provider=self.provider_name,
                endpoint=endpoint,
                from_cache=False,
                latency_ms=elapsed_ms,
                raw_response=response.data,
            )

        except RateLimitError as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            self.health_monitor.record_failure(
                provider=self.provider_name,
                endpoint=endpoint,
                latency_ms=elapsed_ms,
                status_code=429,
                error_type="rate_limit",
            )
            return ProviderResponse(
                success=False,
                data=None,
                provider=self.provider_name,
                endpoint=endpoint,
                latency_ms=elapsed_ms,
                error=f"Rate limit exceeded. Retry after: {e.retry_after}s",
            )

        except HttpError as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            self.health_monitor.record_failure(
                provider=self.provider_name,
                endpoint=endpoint,
                latency_ms=elapsed_ms,
                status_code=e.status_code,
                error_type=type(e).__name__.lower(),
            )
            return ProviderResponse(
                success=False,
                data=None,
                provider=self.provider_name,
                endpoint=endpoint,
                latency_ms=elapsed_ms,
                error=str(e),
            )

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            self.health_monitor.record_failure(
                provider=self.provider_name,
                endpoint=endpoint,
                latency_ms=elapsed_ms,
                error_type="unexpected",
            )
            return ProviderResponse(
                success=False,
                data=None,
                provider=self.provider_name,
                endpoint=endpoint,
                latency_ms=elapsed_ms,
                error=f"Unexpected error: {e}",
            )

    def get_supported_endpoints(self) -> list[str]:
        """
        Get list of supported endpoints.

        Override in subclass to return actual endpoints.

        Returns:
            List of endpoint names
        """
        return []

    def validate_endpoint(self, endpoint: str) -> bool:
        """
        Validate that an endpoint is supported.

        Args:
            endpoint: Endpoint name to validate

        Returns:
            True if endpoint is supported
        """
        supported = self.get_supported_endpoints()
        return not supported or endpoint in supported
