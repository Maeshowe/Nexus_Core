"""
Unit tests for the base data provider.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

import aiohttp

from data_loader.cache import CacheEntry, CacheManager
from data_loader.config import ProviderConfig
from data_loader.health import HealthMonitor
from data_loader.http_client import (
    ClientError,
    HttpClient,
    HttpResponse,
    RateLimitError,
    ServerError,
)
from data_loader.providers.base import BaseDataProvider, ProviderResponse


class MockProvider(BaseDataProvider):
    """Concrete implementation for testing."""

    @property
    def provider_name(self) -> str:
        return "mock"

    async def fetch(self, session, endpoint, **params):
        # Will be mocked in tests
        pass

    def normalize(self, data, endpoint):
        # Simple passthrough for testing
        return data

    def cache_key(self, endpoint, **params):
        return self._generate_cache_key(endpoint, **params)

    def get_supported_endpoints(self):
        return ["test_endpoint", "another_endpoint"]


@pytest.fixture
def provider_config():
    return ProviderConfig(
        api_key="test_api_key",
        base_url="https://api.example.com",
        max_concurrency=5,
        timeout=30.0,
    )


@pytest.fixture
def http_client():
    return HttpClient(timeout=30.0)


@pytest.fixture
def cache_manager(temp_cache_dir):
    return CacheManager(base_dir=temp_cache_dir, ttl_days=7)


@pytest.fixture
def health_monitor():
    return HealthMonitor()


@pytest.fixture
def provider(provider_config, http_client, cache_manager, health_monitor):
    return MockProvider(
        config=provider_config,
        http_client=http_client,
        cache=cache_manager,
        health_monitor=health_monitor,
    )


@pytest.mark.unit
class TestProviderResponse:
    """Tests for ProviderResponse dataclass."""

    def test_create_success_response(self):
        response = ProviderResponse(
            success=True,
            data={"symbol": "AAPL"},
            provider="fmp",
            endpoint="profile",
            from_cache=False,
            latency_ms=150.5,
        )
        assert response.success is True
        assert response.data == {"symbol": "AAPL"}
        assert response.provider == "fmp"
        assert response.from_cache is False

    def test_create_error_response(self):
        response = ProviderResponse(
            success=False,
            data=None,
            provider="fmp",
            endpoint="profile",
            error="Connection failed",
        )
        assert response.success is False
        assert response.data is None
        assert response.error == "Connection failed"

    def test_to_dict(self):
        response = ProviderResponse(
            success=True,
            data={"value": 123},
            provider="polygon",
            endpoint="aggs",
            from_cache=True,
            latency_ms=50.789,
        )
        d = response.to_dict()

        assert d["success"] is True
        assert d["data"] == {"value": 123}
        assert d["provider"] == "polygon"
        assert d["endpoint"] == "aggs"
        assert d["from_cache"] is True
        assert d["latency_ms"] == 50.79  # Rounded


@pytest.mark.unit
class TestBaseDataProvider:
    """Tests for BaseDataProvider class."""

    def test_init(self, provider, provider_config):
        assert provider.config == provider_config
        assert provider.provider_name == "mock"
        assert provider.base_url == "https://api.example.com"
        assert provider.api_key == "test_api_key"

    def test_generate_cache_key_simple(self, provider):
        key = provider._generate_cache_key("profile", symbol="AAPL")
        assert key == "profile_symbol=AAPL"

    def test_generate_cache_key_multiple_params(self, provider):
        key = provider._generate_cache_key(
            "historical",
            symbol="AAPL",
            start="2024-01-01",
            end="2024-01-31",
        )
        # Params should be sorted
        assert "symbol=AAPL" in key
        assert "start=2024-01-01" in key
        assert "end=2024-01-31" in key

    def test_generate_cache_key_no_params(self, provider):
        key = provider._generate_cache_key("screener")
        assert key == "screener"

    def test_generate_cache_key_none_params_ignored(self, provider):
        key = provider._generate_cache_key("profile", symbol="AAPL", extra=None)
        assert key == "profile_symbol=AAPL"

    def test_generate_cache_key_long_key_hashed(self, provider):
        # Create params that would result in a very long key
        long_params = {f"param{i}": f"value{i}" * 20 for i in range(20)}
        key = provider._generate_cache_key("endpoint", **long_params)
        assert len(key) <= 200 + len("endpoint_")

    def test_cache_key(self, provider):
        key = provider.cache_key("test_endpoint", symbol="AAPL")
        assert "test_endpoint" in key
        assert "symbol=AAPL" in key

    def test_get_supported_endpoints(self, provider):
        endpoints = provider.get_supported_endpoints()
        assert "test_endpoint" in endpoints
        assert "another_endpoint" in endpoints

    def test_validate_endpoint_valid(self, provider):
        assert provider.validate_endpoint("test_endpoint") is True

    def test_validate_endpoint_invalid(self, provider):
        assert provider.validate_endpoint("invalid_endpoint") is False

    @pytest.mark.asyncio
    async def test_get_success(self, provider, cache_manager):
        # Mock the fetch method
        mock_response = HttpResponse(
            status=200,
            data={"symbol": "AAPL", "price": 185.50},
            headers={},
            url="https://api.example.com/test",
            elapsed_ms=100.0,
        )
        provider.fetch = AsyncMock(return_value=mock_response)

        async with aiohttp.ClientSession() as session:
            response = await provider.get(session, "test_endpoint", symbol="AAPL")

        assert response.success is True
        assert response.data == {"symbol": "AAPL", "price": 185.50}
        assert response.from_cache is False
        assert response.provider == "mock"

    @pytest.mark.asyncio
    async def test_get_from_cache(self, provider, cache_manager):
        # Pre-populate cache
        cache_manager.set("mock", "test_endpoint_symbol=AAPL", {"cached": True})

        async with aiohttp.ClientSession() as session:
            response = await provider.get(session, "test_endpoint", symbol="AAPL")

        assert response.success is True
        assert response.data == {"cached": True}
        assert response.from_cache is True

    @pytest.mark.asyncio
    async def test_get_bypass_cache(self, provider, cache_manager):
        # Pre-populate cache
        cache_manager.set("mock", "test_endpoint_symbol=AAPL", {"cached": True})

        # Mock fetch
        mock_response = HttpResponse(
            status=200,
            data={"fresh": True},
            headers={},
            url="https://api.example.com/test",
            elapsed_ms=100.0,
        )
        provider.fetch = AsyncMock(return_value=mock_response)

        async with aiohttp.ClientSession() as session:
            response = await provider.get(
                session, "test_endpoint", use_cache=False, symbol="AAPL"
            )

        assert response.success is True
        assert response.data == {"fresh": True}
        assert response.from_cache is False

    @pytest.mark.asyncio
    async def test_get_caches_result(self, provider, cache_manager):
        mock_response = HttpResponse(
            status=200,
            data={"new_data": True},
            headers={},
            url="https://api.example.com/test",
            elapsed_ms=100.0,
        )
        provider.fetch = AsyncMock(return_value=mock_response)

        async with aiohttp.ClientSession() as session:
            await provider.get(session, "test_endpoint", symbol="AAPL")

        # Check cache was populated
        cached = cache_manager.get("mock", "test_endpoint_symbol=AAPL")
        assert cached is not None
        assert cached.data == {"new_data": True}

    @pytest.mark.asyncio
    async def test_get_rate_limit_error(self, provider, health_monitor):
        provider.fetch = AsyncMock(side_effect=RateLimitError(
            "Rate limited", retry_after=60, url="https://api.example.com"
        ))

        async with aiohttp.ClientSession() as session:
            response = await provider.get(session, "test_endpoint", symbol="AAPL")

        assert response.success is False
        assert "Rate limit" in response.error
        assert "60" in response.error

        # Check health monitor recorded failure
        metrics = health_monitor.get_provider_metrics("mock")
        assert metrics.failed_requests == 1
        assert metrics.rate_limited_requests == 1

    @pytest.mark.asyncio
    async def test_get_server_error(self, provider, health_monitor):
        provider.fetch = AsyncMock(side_effect=ServerError(
            "Server error", status_code=500, url="https://api.example.com"
        ))

        async with aiohttp.ClientSession() as session:
            response = await provider.get(session, "test_endpoint", symbol="AAPL")

        assert response.success is False
        assert "Server error" in response.error

        metrics = health_monitor.get_provider_metrics("mock")
        assert metrics.failed_requests == 1

    @pytest.mark.asyncio
    async def test_get_client_error(self, provider, health_monitor):
        provider.fetch = AsyncMock(side_effect=ClientError(
            "Not found", status_code=404, url="https://api.example.com"
        ))

        async with aiohttp.ClientSession() as session:
            response = await provider.get(session, "test_endpoint", symbol="AAPL")

        assert response.success is False
        assert "Not found" in response.error

    @pytest.mark.asyncio
    async def test_get_unexpected_error(self, provider, health_monitor):
        provider.fetch = AsyncMock(side_effect=ValueError("Unexpected"))

        async with aiohttp.ClientSession() as session:
            response = await provider.get(session, "test_endpoint", symbol="AAPL")

        assert response.success is False
        assert "Unexpected" in response.error

        metrics = health_monitor.get_provider_metrics("mock")
        assert metrics.failed_requests == 1

    @pytest.mark.asyncio
    async def test_get_records_health_metrics(self, provider, health_monitor):
        mock_response = HttpResponse(
            status=200,
            data={"data": True},
            headers={},
            url="https://api.example.com/test",
            elapsed_ms=100.0,
        )
        provider.fetch = AsyncMock(return_value=mock_response)

        async with aiohttp.ClientSession() as session:
            await provider.get(session, "test_endpoint", symbol="AAPL")

        metrics = health_monitor.get_provider_metrics("mock")
        assert metrics.total_requests == 1
        assert metrics.successful_requests == 1

    @pytest.mark.asyncio
    async def test_get_includes_raw_response(self, provider):
        raw_data = {"raw": "response", "nested": {"data": True}}
        mock_response = HttpResponse(
            status=200,
            data=raw_data,
            headers={},
            url="https://api.example.com/test",
            elapsed_ms=100.0,
        )
        provider.fetch = AsyncMock(return_value=mock_response)

        async with aiohttp.ClientSession() as session:
            response = await provider.get(session, "test_endpoint")

        assert response.raw_response == raw_data


@pytest.mark.unit
class TestProviderWithNoEndpoints:
    """Test provider that doesn't define supported endpoints."""

    def test_validate_endpoint_empty_list(
        self, provider_config, http_client, cache_manager, health_monitor
    ):
        class EmptyEndpointProvider(BaseDataProvider):
            @property
            def provider_name(self):
                return "empty"

            async def fetch(self, session, endpoint, **params):
                pass

            def normalize(self, data, endpoint):
                return data

            def cache_key(self, endpoint, **params):
                return endpoint

        provider = EmptyEndpointProvider(
            config=provider_config,
            http_client=http_client,
            cache=cache_manager,
            health_monitor=health_monitor,
        )

        # Should return True when no endpoints defined (allow any)
        assert provider.validate_endpoint("any_endpoint") is True
