"""
OmniData Nexus Core - Unified DataLoader

Main entry point for all data retrieval operations. Orchestrates providers,
QoS routing, circuit breaker, retry handling, and caching.
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Optional

import aiohttp

from .cache import CacheManager
from .circuit_breaker import CircuitBreakerConfig, CircuitBreakerError, CircuitBreakerManager, CircuitState
from .config import Config, OperatingMode, load_config
from .health import HealthMonitor, ProviderStatus
from .http_client import HttpClient
from .providers.base import ProviderResponse
from .providers.fmp import FMPProvider
from .providers.fred import FREDProvider
from .providers.polygon import PolygonProvider
from .qos_router import QoSSemaphoreRouter
from .retry import RetryConfig, RetryError, RetryHandler


class ReadOnlyError(Exception):
    """Raised when API call attempted in READ_ONLY mode with cache miss."""

    def __init__(self, provider: str, endpoint: str):
        self.provider = provider
        self.endpoint = endpoint
        super().__init__(
            f"READ_ONLY mode: Cannot fetch from {provider}/{endpoint} - not in cache"
        )


@dataclass
class DataLoaderStats:
    """Statistics for the DataLoader."""

    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    api_calls: int = 0
    api_successes: int = 0
    api_failures: int = 0
    circuit_breaker_rejections: int = 0

    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        if self.total_requests == 0:
            return 0.0
        return self.cache_hits / self.total_requests

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "total_requests": self.total_requests,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "api_calls": self.api_calls,
            "api_successes": self.api_successes,
            "api_failures": self.api_failures,
            "circuit_breaker_rejections": self.circuit_breaker_rejections,
            "cache_hit_rate": round(self.cache_hit_rate, 4),
        }


class DataLoader:
    """
    Unified interface for financial data retrieval.

    Orchestrates all components to provide resilient, cached data access:
    - Providers: FMP, Polygon, FRED
    - QoS Router: Provider-specific concurrency limits
    - Circuit Breaker: Failure isolation and recovery
    - Retry Handler: Exponential backoff for transient failures
    - Cache: Filesystem JSON cache with atomic writes
    - Health Monitor: Request tracking and health reports

    Operating Modes:
    - LIVE: Normal operation, fetches from APIs and caches results
    - READ_ONLY: Only serves from cache, no API calls allowed

    Usage:
        # Create with default configuration
        loader = DataLoader()

        # Or with custom config
        config = load_config()
        loader = DataLoader(config)

        # Fetch data
        async with aiohttp.ClientSession() as session:
            # FMP data
            response = await loader.get_fmp_data(session, "profile", symbol="AAPL")

            # Polygon data
            response = await loader.get_polygon_data(
                session, "aggs_daily",
                ticker="SPY", from_date="2024-01-01", to_date="2024-12-31"
            )

            # FRED data
            response = await loader.get_fred_data(
                session, "series", series_id="CPIAUCSL"
            )

        # Health check
        report = loader.get_api_health_report()
        print(report["overall_status"])

        # Switch modes
        loader.set_operating_mode(OperatingMode.READ_ONLY)
    """

    def __init__(
        self,
        config: Optional[Config] = None,
        qos_router: Optional[QoSSemaphoreRouter] = None,
        circuit_breaker: Optional[CircuitBreakerManager] = None,
        retry_handler: Optional[RetryHandler] = None,
        cache: Optional[CacheManager] = None,
        health_monitor: Optional[HealthMonitor] = None,
    ):
        """
        Initialize DataLoader.

        Args:
            config: Configuration object. If None, loads from environment.
            qos_router: Optional QoS router. If None, creates default.
            circuit_breaker: Optional circuit breaker manager. If None, creates default.
            retry_handler: Optional retry handler. If None, creates default.
            cache: Optional cache manager. If None, creates from config.
            health_monitor: Optional health monitor. If None, creates default.
        """
        # Load configuration
        self.config = config or load_config()

        # Initialize components
        self._qos_router = qos_router or QoSSemaphoreRouter(
            limits={
                "fmp": self.config.fmp.max_concurrency,
                "polygon": self.config.polygon.max_concurrency,
                "fred": self.config.fred.max_concurrency,
            }
        )

        cb_config = CircuitBreakerConfig(
            error_threshold=self.config.circuit_breaker.error_threshold,
            recovery_timeout=self.config.circuit_breaker.recovery_timeout,
            min_requests=self.config.circuit_breaker.min_requests,
        )
        self._circuit_breaker = circuit_breaker or CircuitBreakerManager(
            default_config=cb_config
        )

        retry_config = RetryConfig(
            max_retries=self.config.retry.max_retries,
            base_delay=self.config.retry.base_delay,
            max_delay=self.config.retry.max_delay,
            exponential_base=self.config.retry.exponential_base,
        )
        self._retry_handler = retry_handler or RetryHandler(retry_config)

        self._cache = cache or CacheManager(
            base_dir=self.config.cache.base_dir,
            ttl_days=self.config.cache.ttl_days,
        )

        self._health_monitor = health_monitor or HealthMonitor()

        # Create HTTP client
        self._http_client = HttpClient(timeout=self.config.fmp.timeout)

        # Initialize providers
        self._providers: dict[str, Any] = {}
        self._init_providers()

        # Operating mode
        self._operating_mode = self.config.operating_mode

        # Statistics
        self._stats = DataLoaderStats()

    def _init_providers(self) -> None:
        """Initialize provider instances."""
        self._providers["fmp"] = FMPProvider(
            config=self.config.fmp,
            http_client=self._http_client,
            cache=self._cache,
            health_monitor=self._health_monitor,
        )

        self._providers["polygon"] = PolygonProvider(
            config=self.config.polygon,
            http_client=self._http_client,
            cache=self._cache,
            health_monitor=self._health_monitor,
        )

        self._providers["fred"] = FREDProvider(
            config=self.config.fred,
            http_client=self._http_client,
            cache=self._cache,
            health_monitor=self._health_monitor,
        )

    @property
    def operating_mode(self) -> OperatingMode:
        """Get current operating mode."""
        return self._operating_mode

    def set_operating_mode(self, mode: OperatingMode) -> None:
        """
        Set operating mode.

        Args:
            mode: New operating mode (LIVE or READ_ONLY)
        """
        self._operating_mode = mode

    async def _fetch_with_resilience(
        self,
        session: aiohttp.ClientSession,
        provider_name: str,
        endpoint: str,
        use_cache: bool = True,
        **params,
    ) -> ProviderResponse:
        """
        Fetch data with full resilience stack.

        Flow:
        1. Check operating mode
        2. Check cache (if enabled)
        3. In READ_ONLY mode, return cache or raise error
        4. Check circuit breaker
        5. Acquire QoS semaphore
        6. Execute with retry
        7. Update cache
        8. Record metrics

        Args:
            session: aiohttp ClientSession
            provider_name: Provider name (fmp, polygon, fred)
            endpoint: API endpoint
            use_cache: Whether to use caching
            **params: Endpoint-specific parameters

        Returns:
            ProviderResponse with data or error

        Raises:
            ReadOnlyError: If in READ_ONLY mode and cache miss
            CircuitBreakerError: If circuit is open
        """
        start_time = time.perf_counter()
        self._stats.total_requests += 1

        provider = self._providers.get(provider_name)
        if not provider:
            return ProviderResponse(
                success=False,
                data=None,
                provider=provider_name,
                endpoint=endpoint,
                error=f"Unknown provider: {provider_name}",
            )

        # Generate cache key
        cache_key = provider.cache_key(endpoint, **params)

        # Step 1: Check cache first
        if use_cache:
            cached = self._cache.get(provider_name, cache_key)
            if cached and not cached.is_expired:
                self._stats.cache_hits += 1
                return ProviderResponse(
                    success=True,
                    data=cached.data,
                    provider=provider_name,
                    endpoint=endpoint,
                    from_cache=True,
                    latency_ms=0.0,
                )
            self._stats.cache_misses += 1

        # Step 2: Check operating mode
        if self._operating_mode == OperatingMode.READ_ONLY:
            raise ReadOnlyError(provider_name, endpoint)

        # Step 3: Check circuit breaker
        if not self._circuit_breaker.can_execute(provider_name):
            self._stats.circuit_breaker_rejections += 1
            state = self._circuit_breaker.get_state(provider_name)
            raise CircuitBreakerError(
                f"Circuit breaker {state.value} for {provider_name}",
                state=state,
                provider=provider_name,
            )

        # Step 4: Acquire QoS slot and execute with retry
        async with self._qos_router.acquire(provider_name):
            try:
                self._stats.api_calls += 1

                # Execute with retry handler
                response = await self._retry_handler.execute(
                    provider.get, session, endpoint, use_cache=False, **params
                )

                # Record circuit breaker success
                self._circuit_breaker.record_success(provider_name)
                self._stats.api_successes += 1

                # Cache the result (provider.get() was called with use_cache=False
                # to skip redundant cache check, so we cache here)
                if use_cache and response.success:
                    self._cache.set(provider_name, cache_key, response.data)

                return response

            except RetryError as e:
                # Retries exhausted
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                self._circuit_breaker.record_failure(provider_name)
                self._stats.api_failures += 1

                return ProviderResponse(
                    success=False,
                    data=None,
                    provider=provider_name,
                    endpoint=endpoint,
                    latency_ms=elapsed_ms,
                    error=f"All retries exhausted: {e.last_exception}",
                )

            except Exception as e:
                # Unexpected error
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                self._circuit_breaker.record_failure(provider_name)
                self._stats.api_failures += 1

                return ProviderResponse(
                    success=False,
                    data=None,
                    provider=provider_name,
                    endpoint=endpoint,
                    latency_ms=elapsed_ms,
                    error=f"Unexpected error: {e}",
                )

    async def get_fmp_data(
        self,
        session: aiohttp.ClientSession,
        endpoint: str,
        use_cache: bool = True,
        **params,
    ) -> ProviderResponse:
        """
        Fetch data from FMP provider.

        Supported endpoints:
        - screener: Stock screening with filters
        - profile: Company profile
        - quote: Real-time quote
        - historical_price: Historical OHLCV
        - earnings_calendar: Earnings dates
        - balance_sheet: Balance sheet statements
        - income_statement: Income statements
        - cash_flow: Cash flow statements
        - ratios: Financial ratios
        - growth: Financial growth metrics
        - key_metrics: Key financial metrics
        - insider_trading: Insider trading activity
        - institutional_ownership: Institutional holdings

        Args:
            session: aiohttp ClientSession
            endpoint: API endpoint name
            use_cache: Whether to use caching
            **params: Endpoint-specific parameters (e.g., symbol="AAPL")

        Returns:
            ProviderResponse with data or error
        """
        return await self._fetch_with_resilience(
            session, "fmp", endpoint, use_cache, **params
        )

    async def get_polygon_data(
        self,
        session: aiohttp.ClientSession,
        endpoint: str,
        use_cache: bool = True,
        **params,
    ) -> ProviderResponse:
        """
        Fetch data from Polygon provider.

        Supported endpoints:
        - aggs_daily: Daily OHLCV aggregates
        - trades: Trade data
        - options_snapshot: Options chain snapshot
        - market_snapshot: Market-wide snapshot

        Args:
            session: aiohttp ClientSession
            endpoint: API endpoint name
            use_cache: Whether to use caching
            **params: Endpoint-specific parameters

        Returns:
            ProviderResponse with data or error
        """
        return await self._fetch_with_resilience(
            session, "polygon", endpoint, use_cache, **params
        )

    async def get_fred_data(
        self,
        session: aiohttp.ClientSession,
        endpoint: str,
        use_cache: bool = True,
        **params,
    ) -> ProviderResponse:
        """
        Fetch data from FRED provider.

        Supported endpoints:
        - series: Economic time series data
        - series_info: Series metadata
        - releases: Economic releases list

        Supported series (32 total):
        - Inflation: CPIAUCSL, CPILFESL, PCEPI, PCEPILFE, PPIFIS
        - Labor: UNRATE, PAYEMS, CIVPART, AHETPI, ICSA, CCSA, JTSJOL
        - GDP: GDP, GDPC1, GDI, INDPRO, UMCSENT
        - Housing: CSUSHPINSA, HOUST, PERMIT, HSN1F, EXHOSLUSM495S
        - Interest Rates: FEDFUNDS, DFF, DGS2, DGS10, DGS30, T10Y2Y, T10Y3M
        - Money: M2SL, TOTALSL
        - Financial: VIXCLS

        Args:
            session: aiohttp ClientSession
            endpoint: API endpoint name
            use_cache: Whether to use caching
            **params: Endpoint-specific parameters (e.g., series_id="CPIAUCSL")

        Returns:
            ProviderResponse with data or error
        """
        return await self._fetch_with_resilience(
            session, "fred", endpoint, use_cache, **params
        )

    async def get_data(
        self,
        session: aiohttp.ClientSession,
        provider: str,
        endpoint: str,
        use_cache: bool = True,
        **params,
    ) -> ProviderResponse:
        """
        Generic data fetching method.

        Args:
            session: aiohttp ClientSession
            provider: Provider name (fmp, polygon, fred)
            endpoint: API endpoint
            use_cache: Whether to use caching
            **params: Endpoint-specific parameters

        Returns:
            ProviderResponse with data or error
        """
        return await self._fetch_with_resilience(
            session, provider, endpoint, use_cache, **params
        )

    def get_api_health_report(self) -> dict:
        """
        Get comprehensive health report.

        Returns:
            Dictionary with:
            - timestamp: Report generation time
            - operating_mode: Current mode
            - overall_status: Aggregate health status
            - providers: Per-provider health metrics
            - circuit_breakers: Circuit breaker states
            - qos: QoS statistics
            - loader_stats: DataLoader statistics
        """
        health_report = self._health_monitor.get_health_report()

        # Add circuit breaker states
        cb_states = {}
        for provider in ["fmp", "polygon", "fred"]:
            cb_states[provider] = self._circuit_breaker.get_stats(provider)

        # Add QoS stats
        qos_stats = self._qos_router.get_stats()

        return {
            "timestamp": health_report["timestamp"],
            "operating_mode": self._operating_mode.value,
            "overall_status": health_report["overall_status"],
            "providers": health_report["providers"],
            "circuit_breakers": cb_states,
            "qos": qos_stats,
            "loader_stats": self._stats.to_dict(),
        }

    def get_provider_status(self, provider: str) -> ProviderStatus:
        """
        Get health status for a specific provider.

        Args:
            provider: Provider name

        Returns:
            ProviderStatus enum value
        """
        return self._health_monitor.get_provider_status(provider)

    def is_provider_healthy(self, provider: str) -> bool:
        """
        Check if a provider is healthy.

        Considers both health monitor status and circuit breaker state.

        Args:
            provider: Provider name

        Returns:
            True if provider is healthy
        """
        health_ok = self._health_monitor.is_healthy(provider)
        circuit_ok = self._circuit_breaker.is_healthy(provider)
        return health_ok and circuit_ok

    def get_stats(self) -> DataLoaderStats:
        """Get DataLoader statistics."""
        return self._stats

    def reset_stats(self) -> None:
        """Reset DataLoader statistics."""
        self._stats = DataLoaderStats()

    def reset_circuit_breaker(self, provider: Optional[str] = None) -> None:
        """
        Reset circuit breaker(s).

        Args:
            provider: Optional provider to reset, or None for all
        """
        self._circuit_breaker.reset(provider)

    def reset_health_monitor(self, provider: Optional[str] = None) -> None:
        """
        Reset health monitor metrics.

        Args:
            provider: Optional provider to reset, or None for all
        """
        self._health_monitor.reset(provider)

    def get_supported_endpoints(self, provider: str) -> list[str]:
        """
        Get supported endpoints for a provider.

        Args:
            provider: Provider name

        Returns:
            List of endpoint names
        """
        prov = self._providers.get(provider)
        if prov:
            return prov.get_supported_endpoints()
        return []

    async def close(self) -> None:
        """Close the DataLoader and release resources."""
        await self._http_client.close()


# Convenience function for simple usage
def create_data_loader(
    config: Optional[Config] = None,
) -> DataLoader:
    """
    Create a DataLoader with default configuration.

    Args:
        config: Optional configuration object

    Returns:
        Configured DataLoader instance
    """
    return DataLoader(config)
