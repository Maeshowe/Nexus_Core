"""
Unit tests for the Polygon provider.
"""

import re

import aiohttp
import pytest
from aioresponses import aioresponses

from data_loader.cache import CacheManager
from data_loader.config import ProviderConfig
from data_loader.health import HealthMonitor
from data_loader.http_client import HttpClient
from data_loader.providers.polygon import PolygonProvider, create_polygon_provider


@pytest.fixture
def polygon_config():
    return ProviderConfig(
        api_key="test_polygon_key",
        base_url="https://api.polygon.io",
        max_concurrency=10,
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
def polygon_provider(polygon_config, http_client, cache_manager, health_monitor):
    return PolygonProvider(
        config=polygon_config,
        http_client=http_client,
        cache=cache_manager,
        health_monitor=health_monitor,
    )


@pytest.mark.unit
class TestPolygonProvider:
    """Tests for PolygonProvider class."""

    def test_provider_name(self, polygon_provider):
        assert polygon_provider.provider_name == "polygon"

    def test_supported_endpoints(self, polygon_provider):
        endpoints = polygon_provider.get_supported_endpoints()
        assert len(endpoints) == 4
        assert "aggs_daily" in endpoints
        assert "trades" in endpoints
        assert "options_snapshot" in endpoints
        assert "market_snapshot" in endpoints

    def test_build_url_aggs_daily(self, polygon_provider):
        url = polygon_provider._build_url(
            "aggs_daily", symbol="SPY", start="2024-01-01", end="2024-01-31"
        )
        assert url == "https://api.polygon.io/v2/aggs/ticker/SPY/range/1/day/2024-01-01/2024-01-31"

    def test_build_url_trades(self, polygon_provider):
        url = polygon_provider._build_url("trades", symbol="AAPL")
        assert url == "https://api.polygon.io/v3/trades/AAPL"

    def test_build_url_options_snapshot(self, polygon_provider):
        url = polygon_provider._build_url("options_snapshot", symbol="AAPL")
        assert url == "https://api.polygon.io/v3/snapshot/options/AAPL"

    def test_build_url_market_snapshot(self, polygon_provider):
        url = polygon_provider._build_url("market_snapshot")
        assert url == "https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers"

    def test_build_url_missing_symbol(self, polygon_provider):
        with pytest.raises(ValueError, match="requires 'symbol' parameter"):
            polygon_provider._build_url("aggs_daily", start="2024-01-01", end="2024-01-31")

    def test_build_url_missing_dates(self, polygon_provider):
        with pytest.raises(ValueError, match="requires 'start' parameter"):
            polygon_provider._build_url("aggs_daily", symbol="SPY", end="2024-01-31")

        with pytest.raises(ValueError, match="requires 'end' parameter"):
            polygon_provider._build_url("aggs_daily", symbol="SPY", start="2024-01-01")

    def test_build_url_unknown_endpoint(self, polygon_provider):
        with pytest.raises(ValueError, match="Unknown endpoint"):
            polygon_provider._build_url("unknown_endpoint")

    def test_build_params_includes_api_key(self, polygon_provider):
        params = polygon_provider._build_params("aggs_daily")
        assert "apiKey" in params
        assert params["apiKey"] == "test_polygon_key"

    def test_build_params_filters_allowed(self, polygon_provider):
        params = polygon_provider._build_params(
            "aggs_daily",
            adjusted=True,
            sort="asc",
            limit=100,
            invalid="ignored",
        )
        assert params["adjusted"] is True
        assert params["sort"] == "asc"
        assert params["limit"] == 100
        assert "invalid" not in params

    def test_cache_key_simple(self, polygon_provider):
        key = polygon_provider.cache_key("trades", symbol="AAPL")
        assert "trades" in key
        assert "symbol=AAPL" in key
        assert "apiKey" not in key

    def test_cache_key_with_dates(self, polygon_provider):
        key = polygon_provider.cache_key(
            "aggs_daily", symbol="SPY", start="2024-01-01", end="2024-01-31"
        )
        assert "aggs_daily" in key
        assert "symbol=SPY" in key
        assert "start=2024-01-01" in key
        assert "end=2024-01-31" in key

    def test_validate_symbol_valid(self, polygon_provider):
        assert polygon_provider.validate_symbol("SPY") is True
        assert polygon_provider.validate_symbol("AAPL") is True
        assert polygon_provider.validate_symbol("BRK.A") is True
        # Options symbol format
        assert polygon_provider.validate_symbol("O:AAPL230120C00150000") is True

    def test_validate_symbol_invalid(self, polygon_provider):
        assert polygon_provider.validate_symbol("") is False
        assert polygon_provider.validate_symbol(None) is False
        assert polygon_provider.validate_symbol("INVALID!") is False


@pytest.mark.unit
class TestPolygonProviderNormalize:
    """Tests for Polygon response normalization."""

    def test_normalize_aggs_daily(self, polygon_provider):
        data = {
            "ticker": "SPY",
            "queryCount": 5,
            "resultsCount": 5,
            "adjusted": True,
            "status": "OK",
            "results": [
                {"o": 450.0, "h": 452.0, "l": 449.0, "c": 451.5, "v": 1000000},
            ]
        }
        result = polygon_provider.normalize(data, "aggs_daily")
        assert result["ticker"] == "SPY"
        assert result["resultsCount"] == 5
        assert len(result["results"]) == 1

    def test_normalize_trades(self, polygon_provider):
        data = {
            "status": "OK",
            "results": [
                {"price": 185.50, "size": 100},
                {"price": 185.51, "size": 200},
            ],
            "next_url": "https://api.polygon.io/v3/trades/AAPL?cursor=abc123"
        }
        result = polygon_provider.normalize(data, "trades")
        assert len(result["results"]) == 2
        assert result["next_url"] is not None

    def test_normalize_options_snapshot(self, polygon_provider):
        data = {
            "status": "OK",
            "results": [
                {"strike_price": 150.0, "contract_type": "call"},
            ]
        }
        result = polygon_provider.normalize(data, "options_snapshot")
        assert len(result["results"]) == 1

    def test_normalize_market_snapshot(self, polygon_provider):
        data = {
            "status": "OK",
            "tickers": [
                {"ticker": "AAPL", "todaysChange": 1.5},
                {"ticker": "MSFT", "todaysChange": -0.5},
            ],
            "count": 2
        }
        result = polygon_provider.normalize(data, "market_snapshot")
        assert len(result["tickers"]) == 2
        assert result["count"] == 2

    def test_normalize_error_response(self, polygon_provider):
        data = {
            "status": "ERROR",
            "error": "Invalid API key",
            "message": "Please provide a valid API key"
        }
        result = polygon_provider.normalize(data, "aggs_daily")
        assert result["error"] == "Invalid API key"
        assert result["data"] is None


@pytest.mark.unit
class TestPolygonProviderFetch:
    """Tests for Polygon API fetching."""

    @pytest.mark.asyncio
    async def test_fetch_aggs_daily_success(self, polygon_provider):
        url_pattern = re.compile(r'https://api\.polygon\.io/v2/aggs/ticker/SPY/range/1/day/2024-01-01/2024-01-31.*')

        with aioresponses() as m:
            m.get(
                url_pattern,
                payload={
                    "status": "OK",
                    "ticker": "SPY",
                    "resultsCount": 1,
                    "results": [{"o": 450.0, "c": 451.0}]
                },
                status=200,
            )

            async with aiohttp.ClientSession() as session:
                response = await polygon_provider.fetch(
                    session, "aggs_daily",
                    symbol="SPY", start="2024-01-01", end="2024-01-31"
                )

            assert response.status == 200
            assert response.data["ticker"] == "SPY"

    @pytest.mark.asyncio
    async def test_fetch_invalid_endpoint(self, polygon_provider):
        async with aiohttp.ClientSession() as session:
            with pytest.raises(ValueError, match="Invalid endpoint"):
                await polygon_provider.fetch(session, "invalid_endpoint")


@pytest.mark.unit
class TestPolygonProviderIntegration:
    """Integration tests for Polygon provider get method."""

    @pytest.mark.asyncio
    async def test_get_aggs_daily_success(self, polygon_provider):
        url_pattern = re.compile(r'https://api\.polygon\.io/v2/aggs/ticker/AAPL/range/1/day/2024-01-01/2024-01-31.*')

        with aioresponses() as m:
            m.get(
                url_pattern,
                payload={
                    "status": "OK",
                    "ticker": "AAPL",
                    "adjusted": True,
                    "queryCount": 22,
                    "resultsCount": 22,
                    "results": [{"o": 185.0, "h": 186.0, "l": 184.0, "c": 185.5}]
                },
                status=200,
            )

            async with aiohttp.ClientSession() as session:
                response = await polygon_provider.get(
                    session, "aggs_daily",
                    symbol="AAPL", start="2024-01-01", end="2024-01-31"
                )

            assert response.success is True
            assert response.data["ticker"] == "AAPL"
            assert response.from_cache is False

    @pytest.mark.asyncio
    async def test_get_from_cache(self, polygon_provider, cache_manager):
        # Pre-populate cache
        cache_key = "aggs_daily_end=2024-01-31_start=2024-01-01_symbol=SPY"
        cache_manager.set("polygon", cache_key, {"ticker": "SPY", "cached": True})

        async with aiohttp.ClientSession() as session:
            response = await polygon_provider.get(
                session, "aggs_daily",
                symbol="SPY", start="2024-01-01", end="2024-01-31"
            )

        assert response.success is True
        assert response.data["cached"] is True
        assert response.from_cache is True

    @pytest.mark.asyncio
    async def test_get_records_health_metrics(self, polygon_provider, health_monitor):
        url_pattern = re.compile(r'https://api\.polygon\.io/v3/trades/MSFT.*')

        with aioresponses() as m:
            m.get(
                url_pattern,
                payload={"status": "OK", "results": []},
                status=200,
            )

            async with aiohttp.ClientSession() as session:
                await polygon_provider.get(session, "trades", symbol="MSFT")

        metrics = health_monitor.get_provider_metrics("polygon")
        assert metrics.total_requests == 1
        assert metrics.successful_requests == 1


@pytest.mark.unit
class TestCreatePolygonProvider:
    """Tests for the create_polygon_provider convenience function."""

    def test_create_provider(self, temp_cache_dir):
        provider = create_polygon_provider(
            api_key="test_key",
            cache_dir=str(temp_cache_dir),
            timeout=60.0,
        )

        assert provider.provider_name == "polygon"
        assert provider.api_key == "test_key"
        assert provider.config.timeout == 60.0
        assert provider.config.max_concurrency == 10

    def test_create_provider_default_cache(self):
        provider = create_polygon_provider(api_key="test_key")
        assert provider.provider_name == "polygon"
