"""
Unit tests for the unified DataLoader interface.
"""

import re

import pytest

import aiohttp
from aioresponses import aioresponses

from data_loader.cache import CacheManager
from data_loader.circuit_breaker import (
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitBreakerManager,
    CircuitState,
)
from data_loader.config import Config, OperatingMode
from data_loader.health import HealthMonitor, ProviderStatus
from data_loader.loader import DataLoader, DataLoaderStats, ReadOnlyError, create_data_loader
from data_loader.qos_router import QoSSemaphoreRouter
from data_loader.retry import RetryConfig, RetryHandler


@pytest.fixture
def mock_config(temp_cache_dir):
    """Create a mock config for testing."""
    return Config.from_env()


@pytest.fixture
def data_loader(temp_cache_dir, mock_config):
    """Create a DataLoader instance for testing."""
    cache = CacheManager(base_dir=temp_cache_dir, ttl_days=7)
    return DataLoader(
        config=mock_config,
        cache=cache,
    )


@pytest.mark.unit
class TestDataLoaderInit:
    """Tests for DataLoader initialization."""

    def test_creates_with_default_config(self, temp_cache_dir):
        loader = DataLoader()
        assert loader.config is not None
        assert loader.operating_mode == OperatingMode.LIVE

    def test_creates_with_custom_config(self, mock_config, temp_cache_dir):
        cache = CacheManager(base_dir=temp_cache_dir)
        loader = DataLoader(config=mock_config, cache=cache)
        assert loader.config == mock_config

    def test_creates_with_custom_components(self, mock_config, temp_cache_dir):
        cache = CacheManager(base_dir=temp_cache_dir)
        qos = QoSSemaphoreRouter(limits={"fmp": 5})
        cb = CircuitBreakerManager()
        retry = RetryHandler(RetryConfig(max_retries=2))
        health = HealthMonitor()

        loader = DataLoader(
            config=mock_config,
            qos_router=qos,
            circuit_breaker=cb,
            retry_handler=retry,
            cache=cache,
            health_monitor=health,
        )

        assert loader._qos_router == qos
        assert loader._circuit_breaker == cb
        assert loader._retry_handler == retry
        assert loader._cache == cache
        assert loader._health_monitor == health

    def test_initializes_all_providers(self, data_loader):
        assert "fmp" in data_loader._providers
        assert "polygon" in data_loader._providers
        assert "fred" in data_loader._providers


@pytest.mark.unit
class TestOperatingMode:
    """Tests for operating mode handling."""

    def test_default_mode_is_live(self, data_loader):
        assert data_loader.operating_mode == OperatingMode.LIVE

    def test_set_operating_mode_to_read_only(self, data_loader):
        data_loader.set_operating_mode(OperatingMode.READ_ONLY)
        assert data_loader.operating_mode == OperatingMode.READ_ONLY

    def test_set_operating_mode_to_live(self, data_loader):
        data_loader.set_operating_mode(OperatingMode.READ_ONLY)
        data_loader.set_operating_mode(OperatingMode.LIVE)
        assert data_loader.operating_mode == OperatingMode.LIVE

    @pytest.mark.asyncio
    async def test_read_only_mode_raises_on_cache_miss(self, data_loader):
        data_loader.set_operating_mode(OperatingMode.READ_ONLY)

        async with aiohttp.ClientSession() as session:
            with pytest.raises(ReadOnlyError) as exc_info:
                await data_loader.get_fmp_data(session, "profile", symbol="AAPL")

        assert exc_info.value.provider == "fmp"
        assert exc_info.value.endpoint == "profile"
        assert "READ_ONLY mode" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_read_only_mode_returns_cached_data(self, data_loader, temp_cache_dir):
        # Pre-populate cache
        cache_key = data_loader._providers["fmp"].cache_key("profile", symbol="AAPL")
        data_loader._cache.set("fmp", cache_key, {"symbol": "AAPL", "cached": True})

        data_loader.set_operating_mode(OperatingMode.READ_ONLY)

        async with aiohttp.ClientSession() as session:
            response = await data_loader.get_fmp_data(session, "profile", symbol="AAPL")

        assert response.success is True
        assert response.from_cache is True
        assert response.data["cached"] is True


@pytest.mark.unit
class TestCacheHandling:
    """Tests for cache behavior."""

    @pytest.mark.asyncio
    async def test_returns_cached_data_on_cache_hit(self, data_loader):
        # Pre-populate cache
        cache_key = data_loader._providers["fmp"].cache_key("profile", symbol="MSFT")
        data_loader._cache.set("fmp", cache_key, {"symbol": "MSFT", "name": "Microsoft"})

        async with aiohttp.ClientSession() as session:
            response = await data_loader.get_fmp_data(session, "profile", symbol="MSFT")

        assert response.success is True
        assert response.from_cache is True
        assert response.data["symbol"] == "MSFT"

    @pytest.mark.asyncio
    async def test_cache_stats_tracked(self, data_loader):
        # Pre-populate cache
        cache_key = data_loader._providers["fmp"].cache_key("profile", symbol="GOOG")
        data_loader._cache.set("fmp", cache_key, {"symbol": "GOOG"})

        async with aiohttp.ClientSession() as session:
            await data_loader.get_fmp_data(session, "profile", symbol="GOOG")

        stats = data_loader.get_stats()
        assert stats.cache_hits == 1
        assert stats.total_requests == 1

    @pytest.mark.asyncio
    async def test_cache_bypass_when_disabled(self, data_loader):
        # Pre-populate cache
        cache_key = data_loader._providers["fmp"].cache_key("profile", symbol="AMZN")
        data_loader._cache.set("fmp", cache_key, {"symbol": "AMZN", "cached": True})

        url_pattern = re.compile(r'https://financialmodelingprep\.com/stable/profile\?.*')

        with aioresponses() as m:
            m.get(
                url_pattern,
                payload=[{"symbol": "AMZN", "name": "Amazon", "fresh": True}],
                status=200,
            )

            async with aiohttp.ClientSession() as session:
                response = await data_loader.get_fmp_data(
                    session, "profile", symbol="AMZN", use_cache=False
                )

        # Should have fetched from API (fresh data)
        assert response.success is True
        assert response.from_cache is False


@pytest.mark.unit
class TestCircuitBreakerIntegration:
    """Tests for circuit breaker integration."""

    @pytest.mark.asyncio
    async def test_rejects_when_circuit_open(self, data_loader):
        # Force circuit breaker open
        for _ in range(15):
            data_loader._circuit_breaker.record_failure("fmp")

        async with aiohttp.ClientSession() as session:
            with pytest.raises(CircuitBreakerError) as exc_info:
                await data_loader.get_fmp_data(session, "profile", symbol="AAPL")

        assert exc_info.value.provider == "fmp"
        assert data_loader._stats.circuit_breaker_rejections >= 1

    @pytest.mark.asyncio
    async def test_circuit_breaker_state_affects_requests(self, data_loader):
        # Record enough failures to open circuit
        for _ in range(15):
            data_loader._circuit_breaker.record_failure("polygon")

        assert data_loader._circuit_breaker.get_state("polygon") == CircuitState.OPEN

        async with aiohttp.ClientSession() as session:
            with pytest.raises(CircuitBreakerError):
                await data_loader.get_polygon_data(
                    session, "aggs_daily",
                    symbol="SPY", start="2024-01-01", end="2024-01-31"
                )


@pytest.mark.unit
class TestFMPDataFetching:
    """Tests for FMP data fetching."""

    @pytest.mark.asyncio
    async def test_get_fmp_profile(self, data_loader):
        url_pattern = re.compile(r'https://financialmodelingprep\.com/stable/profile\?.*')

        with aioresponses() as m:
            m.get(
                url_pattern,
                payload=[{
                    "symbol": "AAPL",
                    "companyName": "Apple Inc.",
                    "sector": "Technology",
                }],
                status=200,
            )

            async with aiohttp.ClientSession() as session:
                response = await data_loader.get_fmp_data(
                    session, "profile", symbol="AAPL"
                )

        assert response.success is True
        assert response.provider == "fmp"
        assert response.endpoint == "profile"
        assert response.from_cache is False

    @pytest.mark.asyncio
    async def test_get_fmp_quote(self, data_loader):
        url_pattern = re.compile(r'https://financialmodelingprep\.com/stable/quote\?.*')

        with aioresponses() as m:
            m.get(
                url_pattern,
                payload=[{
                    "symbol": "MSFT",
                    "price": 400.00,
                    "change": 5.00,
                }],
                status=200,
            )

            async with aiohttp.ClientSession() as session:
                response = await data_loader.get_fmp_data(
                    session, "quote", symbol="MSFT"
                )

        assert response.success is True
        assert response.data["symbol"] == "MSFT"


@pytest.mark.unit
class TestPolygonDataFetching:
    """Tests for Polygon data fetching."""

    @pytest.mark.asyncio
    async def test_get_polygon_aggs(self, data_loader):
        url_pattern = re.compile(r'https://api\.polygon\.io/v2/aggs/ticker/SPY/range/1/day/.*')

        with aioresponses() as m:
            m.get(
                url_pattern,
                payload={
                    "ticker": "SPY",
                    "resultsCount": 5,
                    "results": [
                        {"o": 450.0, "h": 455.0, "l": 448.0, "c": 452.0, "v": 1000000}
                    ],
                },
                status=200,
            )

            async with aiohttp.ClientSession() as session:
                response = await data_loader.get_polygon_data(
                    session, "aggs_daily",
                    symbol="SPY", start="2024-01-01", end="2024-01-31"
                )

        assert response.success is True
        assert response.provider == "polygon"


@pytest.mark.unit
class TestFREDDataFetching:
    """Tests for FRED data fetching."""

    @pytest.mark.asyncio
    async def test_get_fred_series(self, data_loader):
        url_pattern = re.compile(r'https://api\.stlouisfed\.org/fred/series/observations.*')

        with aioresponses() as m:
            m.get(
                url_pattern,
                payload={
                    "count": 1,
                    "observations": [
                        {"date": "2024-01-01", "value": "308.417"},
                    ],
                },
                status=200,
            )

            async with aiohttp.ClientSession() as session:
                response = await data_loader.get_fred_data(
                    session, "series", series_id="CPIAUCSL"
                )

        assert response.success is True
        assert response.provider == "fred"


@pytest.mark.unit
class TestGenericDataFetching:
    """Tests for the generic get_data method."""

    @pytest.mark.asyncio
    async def test_get_data_with_fmp(self, data_loader):
        url_pattern = re.compile(r'https://financialmodelingprep\.com/stable/profile\?.*')

        with aioresponses() as m:
            m.get(
                url_pattern,
                payload=[{"symbol": "TSLA", "companyName": "Tesla"}],
                status=200,
            )

            async with aiohttp.ClientSession() as session:
                response = await data_loader.get_data(
                    session, "fmp", "profile", symbol="TSLA"
                )

        assert response.success is True
        assert response.provider == "fmp"

    @pytest.mark.asyncio
    async def test_get_data_unknown_provider(self, data_loader):
        async with aiohttp.ClientSession() as session:
            response = await data_loader.get_data(
                session, "unknown_provider", "endpoint"
            )

        assert response.success is False
        assert "Unknown provider" in response.error


@pytest.mark.unit
class TestHealthReport:
    """Tests for health reporting."""

    def test_get_api_health_report_structure(self, data_loader):
        report = data_loader.get_api_health_report()

        assert "timestamp" in report
        assert "operating_mode" in report
        assert "overall_status" in report
        assert "providers" in report
        assert "circuit_breakers" in report
        assert "qos" in report
        assert "loader_stats" in report

    def test_health_report_includes_all_providers(self, data_loader):
        report = data_loader.get_api_health_report()

        assert "fmp" in report["providers"]
        assert "polygon" in report["providers"]
        assert "fred" in report["providers"]

    def test_get_provider_status(self, data_loader):
        status = data_loader.get_provider_status("fmp")
        assert isinstance(status, ProviderStatus)

    def test_is_provider_healthy_when_healthy(self, data_loader):
        assert data_loader.is_provider_healthy("fmp") is True

    def test_is_provider_healthy_when_circuit_open(self, data_loader):
        # Force circuit open
        for _ in range(15):
            data_loader._circuit_breaker.record_failure("polygon")

        assert data_loader.is_provider_healthy("polygon") is False


@pytest.mark.unit
class TestStatistics:
    """Tests for statistics tracking."""

    def test_initial_stats_are_zero(self, data_loader):
        stats = data_loader.get_stats()
        assert stats.total_requests == 0
        assert stats.cache_hits == 0
        assert stats.cache_misses == 0
        assert stats.api_calls == 0

    @pytest.mark.asyncio
    async def test_stats_track_cache_hits(self, data_loader):
        # Pre-populate cache
        cache_key = data_loader._providers["fred"].cache_key("series", series_id="GDP")
        data_loader._cache.set("fred", cache_key, {"observations": []})

        async with aiohttp.ClientSession() as session:
            await data_loader.get_fred_data(session, "series", series_id="GDP")

        stats = data_loader.get_stats()
        assert stats.cache_hits == 1
        assert stats.total_requests == 1

    @pytest.mark.asyncio
    async def test_stats_track_api_calls(self, data_loader):
        url_pattern = re.compile(r'https://financialmodelingprep\.com/stable/profile\?.*')

        with aioresponses() as m:
            m.get(
                url_pattern,
                payload=[{"symbol": "NVDA"}],
                status=200,
            )

            async with aiohttp.ClientSession() as session:
                await data_loader.get_fmp_data(session, "profile", symbol="NVDA")

        stats = data_loader.get_stats()
        assert stats.api_calls == 1
        assert stats.api_successes == 1
        assert stats.cache_misses == 1

    def test_reset_stats(self, data_loader):
        data_loader._stats.total_requests = 100
        data_loader._stats.cache_hits = 50

        data_loader.reset_stats()

        stats = data_loader.get_stats()
        assert stats.total_requests == 0
        assert stats.cache_hits == 0

    def test_cache_hit_rate_calculation(self):
        stats = DataLoaderStats()
        stats.total_requests = 100
        stats.cache_hits = 75

        assert stats.cache_hit_rate == 0.75

    def test_cache_hit_rate_when_no_requests(self):
        stats = DataLoaderStats()
        assert stats.cache_hit_rate == 0.0


@pytest.mark.unit
class TestResetMethods:
    """Tests for reset functionality."""

    def test_reset_circuit_breaker_single_provider(self, data_loader):
        # Force circuit open
        for _ in range(15):
            data_loader._circuit_breaker.record_failure("fmp")

        assert data_loader._circuit_breaker.get_state("fmp") == CircuitState.OPEN

        data_loader.reset_circuit_breaker("fmp")

        assert data_loader._circuit_breaker.get_state("fmp") == CircuitState.CLOSED

    def test_reset_circuit_breaker_all_providers(self, data_loader):
        # Force circuits open
        for _ in range(15):
            data_loader._circuit_breaker.record_failure("fmp")
            data_loader._circuit_breaker.record_failure("polygon")

        data_loader.reset_circuit_breaker()

        assert data_loader._circuit_breaker.get_state("fmp") == CircuitState.CLOSED
        assert data_loader._circuit_breaker.get_state("polygon") == CircuitState.CLOSED

    def test_reset_health_monitor(self, data_loader):
        data_loader._health_monitor.record_success("fmp", "profile", 100.0)

        data_loader.reset_health_monitor("fmp")

        metrics = data_loader._health_monitor.get_provider_metrics("fmp")
        assert metrics.total_requests == 0


@pytest.mark.unit
class TestSupportedEndpoints:
    """Tests for getting supported endpoints."""

    def test_get_supported_fmp_endpoints(self, data_loader):
        endpoints = data_loader.get_supported_endpoints("fmp")
        assert "profile" in endpoints
        assert "quote" in endpoints
        assert "historical_price" in endpoints

    def test_get_supported_polygon_endpoints(self, data_loader):
        endpoints = data_loader.get_supported_endpoints("polygon")
        assert "aggs_daily" in endpoints
        assert "trades" in endpoints

    def test_get_supported_fred_endpoints(self, data_loader):
        endpoints = data_loader.get_supported_endpoints("fred")
        assert "series" in endpoints
        assert "series_info" in endpoints

    def test_get_supported_endpoints_unknown_provider(self, data_loader):
        endpoints = data_loader.get_supported_endpoints("unknown")
        assert endpoints == []


@pytest.mark.unit
class TestCreateDataLoader:
    """Tests for the create_data_loader convenience function."""

    def test_create_data_loader_default(self):
        loader = create_data_loader()
        assert loader is not None
        assert isinstance(loader, DataLoader)

    def test_create_data_loader_with_config(self, mock_config):
        loader = create_data_loader(config=mock_config)
        assert loader.config == mock_config


@pytest.mark.unit
class TestDataLoaderStatsDict:
    """Tests for DataLoaderStats to_dict method."""

    def test_stats_to_dict(self):
        stats = DataLoaderStats(
            total_requests=100,
            cache_hits=60,
            cache_misses=40,
            api_calls=40,
            api_successes=35,
            api_failures=5,
            circuit_breaker_rejections=2,
        )

        result = stats.to_dict()

        assert result["total_requests"] == 100
        assert result["cache_hits"] == 60
        assert result["cache_misses"] == 40
        assert result["api_calls"] == 40
        assert result["api_successes"] == 35
        assert result["api_failures"] == 5
        assert result["circuit_breaker_rejections"] == 2
        assert result["cache_hit_rate"] == 0.6


@pytest.mark.unit
class TestReadOnlyError:
    """Tests for ReadOnlyError exception."""

    def test_read_only_error_attributes(self):
        error = ReadOnlyError("fmp", "profile")

        assert error.provider == "fmp"
        assert error.endpoint == "profile"

    def test_read_only_error_message(self):
        error = ReadOnlyError("polygon", "aggs_daily")
        message = str(error)

        assert "READ_ONLY mode" in message
        assert "polygon" in message
        assert "aggs_daily" in message
