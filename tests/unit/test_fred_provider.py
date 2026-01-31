"""
Unit tests for the FRED provider.
"""

import re

import pytest

import aiohttp
from aioresponses import aioresponses

from data_loader.cache import CacheManager
from data_loader.config import ProviderConfig
from data_loader.health import HealthMonitor
from data_loader.http_client import HttpClient
from data_loader.providers.fred import FREDProvider, create_fred_provider


@pytest.fixture
def fred_config():
    return ProviderConfig(
        api_key="test_fred_key",
        base_url="https://api.stlouisfed.org/fred",
        max_concurrency=1,
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
def fred_provider(fred_config, http_client, cache_manager, health_monitor):
    return FREDProvider(
        config=fred_config,
        http_client=http_client,
        cache=cache_manager,
        health_monitor=health_monitor,
    )


@pytest.mark.unit
class TestFREDProvider:
    """Tests for FREDProvider class."""

    def test_provider_name(self, fred_provider):
        assert fred_provider.provider_name == "fred"

    def test_supported_endpoints(self, fred_provider):
        endpoints = fred_provider.get_supported_endpoints()
        assert "series" in endpoints
        assert "series_info" in endpoints
        assert "releases" in endpoints

    def test_supported_series(self, fred_provider):
        series = fred_provider.get_supported_series()
        assert len(series) == 32
        assert "CPIAUCSL" in series
        assert "UNRATE" in series
        assert "GDP" in series
        assert "FEDFUNDS" in series
        assert "DGS10" in series

    def test_build_url_series(self, fred_provider):
        url = fred_provider._build_url("series")
        assert url == "https://api.stlouisfed.org/fred/series/observations"

    def test_build_url_series_info(self, fred_provider):
        url = fred_provider._build_url("series_info")
        assert url == "https://api.stlouisfed.org/fred/series"

    def test_build_url_releases(self, fred_provider):
        url = fred_provider._build_url("releases")
        assert url == "https://api.stlouisfed.org/fred/releases"

    def test_build_url_unknown_endpoint(self, fred_provider):
        with pytest.raises(ValueError, match="Unknown endpoint"):
            fred_provider._build_url("unknown_endpoint")

    def test_build_params_includes_api_key(self, fred_provider):
        params = fred_provider._build_params("series")
        assert "api_key" in params
        assert params["api_key"] == "test_fred_key"
        assert params["file_type"] == "json"

    def test_build_params_filters_allowed(self, fred_provider):
        params = fred_provider._build_params(
            "series",
            series_id="CPIAUCSL",
            observation_start="2024-01-01",
            observation_end="2024-12-31",
            units="lin",
            invalid="ignored",
        )
        assert params["series_id"] == "CPIAUCSL"
        assert params["observation_start"] == "2024-01-01"
        assert params["observation_end"] == "2024-12-31"
        assert params["units"] == "lin"
        assert "invalid" not in params

    def test_cache_key_simple(self, fred_provider):
        key = fred_provider.cache_key("series", series_id="CPIAUCSL")
        assert "series" in key
        assert "series_id=CPIAUCSL" in key
        assert "api_key" not in key

    def test_cache_key_with_dates(self, fred_provider):
        key = fred_provider.cache_key(
            "series",
            series_id="GDP",
            observation_start="2024-01-01",
            observation_end="2024-12-31",
        )
        assert "series" in key
        assert "series_id=GDP" in key
        assert "observation_start=2024-01-01" in key

    def test_validate_series_id_valid(self, fred_provider):
        assert fred_provider.validate_series_id("CPIAUCSL") is True
        assert fred_provider.validate_series_id("GDP") is True
        assert fred_provider.validate_series_id("DGS10") is True
        assert fred_provider.validate_series_id("T10Y2Y") is True

    def test_validate_series_id_invalid(self, fred_provider):
        assert fred_provider.validate_series_id("") is False
        assert fred_provider.validate_series_id(None) is False
        assert fred_provider.validate_series_id("INVALID!") is False

    def test_is_supported_series(self, fred_provider):
        assert fred_provider.is_supported_series("CPIAUCSL") is True
        assert fred_provider.is_supported_series("cpiaucsl") is True  # Case insensitive
        assert fred_provider.is_supported_series("UNKNOWN123") is False


@pytest.mark.unit
class TestFREDProviderNormalize:
    """Tests for FRED response normalization."""

    def test_normalize_series(self, fred_provider):
        data = {
            "realtime_start": "2024-01-01",
            "realtime_end": "2024-12-31",
            "observation_start": "2024-01-01",
            "observation_end": "2024-12-31",
            "units": "lin",
            "output_type": 1,
            "count": 12,
            "observations": [
                {"date": "2024-01-01", "value": "308.417"},
                {"date": "2024-02-01", "value": "309.685"},
            ]
        }
        result = fred_provider.normalize(data, "series")
        assert result["count"] == 12
        assert len(result["observations"]) == 2
        assert result["realtime_start"] == "2024-01-01"

    def test_normalize_series_info(self, fred_provider):
        data = {
            "seriess": [{
                "id": "CPIAUCSL",
                "title": "Consumer Price Index for All Urban Consumers",
                "frequency": "Monthly",
                "units": "Index 1982-1984=100",
            }]
        }
        result = fred_provider.normalize(data, "series_info")
        # Single series should be unwrapped
        assert result["id"] == "CPIAUCSL"
        assert result["frequency"] == "Monthly"

    def test_normalize_releases(self, fred_provider):
        data = {
            "count": 2,
            "releases": [
                {"id": 10, "name": "Consumer Price Index"},
                {"id": 53, "name": "Gross Domestic Product"},
            ]
        }
        result = fred_provider.normalize(data, "releases")
        assert result["count"] == 2
        assert len(result["releases"]) == 2

    def test_normalize_error_response(self, fred_provider):
        data = {
            "error_code": 400,
            "error_message": "Bad Request. series_id is required"
        }
        result = fred_provider.normalize(data, "series")
        assert result["error"] == "Bad Request. series_id is required"
        assert result["error_code"] == 400
        assert result["data"] is None


@pytest.mark.unit
class TestFREDProviderFetch:
    """Tests for FRED API fetching."""

    @pytest.mark.asyncio
    async def test_fetch_series_success(self, fred_provider):
        url_pattern = re.compile(r'https://api\.stlouisfed\.org/fred/series/observations.*')

        with aioresponses() as m:
            m.get(
                url_pattern,
                payload={
                    "count": 1,
                    "observations": [{"date": "2024-01-01", "value": "308.417"}]
                },
                status=200,
            )

            async with aiohttp.ClientSession() as session:
                response = await fred_provider.fetch(
                    session, "series", series_id="CPIAUCSL"
                )

            assert response.status == 200
            assert response.data["count"] == 1

    @pytest.mark.asyncio
    async def test_fetch_missing_series_id(self, fred_provider):
        async with aiohttp.ClientSession() as session:
            with pytest.raises(ValueError, match="requires 'series_id' parameter"):
                await fred_provider.fetch(session, "series")

    @pytest.mark.asyncio
    async def test_fetch_invalid_endpoint(self, fred_provider):
        async with aiohttp.ClientSession() as session:
            with pytest.raises(ValueError, match="Invalid endpoint"):
                await fred_provider.fetch(session, "invalid_endpoint")


@pytest.mark.unit
class TestFREDProviderIntegration:
    """Integration tests for FRED provider get method."""

    @pytest.mark.asyncio
    async def test_get_series_success(self, fred_provider):
        url_pattern = re.compile(r'https://api\.stlouisfed\.org/fred/series/observations.*')

        with aioresponses() as m:
            m.get(
                url_pattern,
                payload={
                    "realtime_start": "2024-01-01",
                    "realtime_end": "2024-12-31",
                    "count": 12,
                    "observations": [
                        {"date": "2024-01-01", "value": "308.417"},
                    ]
                },
                status=200,
            )

            async with aiohttp.ClientSession() as session:
                response = await fred_provider.get(
                    session, "series", series_id="CPIAUCSL"
                )

            assert response.success is True
            assert response.data["count"] == 12
            assert response.from_cache is False

    @pytest.mark.asyncio
    async def test_get_series_convenience_method(self, fred_provider):
        url_pattern = re.compile(r'https://api\.stlouisfed\.org/fred/series/observations.*')

        with aioresponses() as m:
            m.get(
                url_pattern,
                payload={
                    "count": 1,
                    "observations": [{"date": "2024-01-01", "value": "3.7"}]
                },
                status=200,
            )

            async with aiohttp.ClientSession() as session:
                response = await fred_provider.get_series(
                    session,
                    series_id="UNRATE",
                    start_date="2024-01-01",
                    end_date="2024-12-31",
                )

            assert response.success is True
            assert len(response.data["observations"]) == 1

    @pytest.mark.asyncio
    async def test_get_from_cache(self, fred_provider, cache_manager):
        # Pre-populate cache
        cache_key = "series_series_id=CPIAUCSL"
        cache_manager.set("fred", cache_key, {"count": 10, "cached": True})

        async with aiohttp.ClientSession() as session:
            response = await fred_provider.get(
                session, "series", series_id="CPIAUCSL"
            )

        assert response.success is True
        assert response.data["cached"] is True
        assert response.from_cache is True

    @pytest.mark.asyncio
    async def test_get_records_health_metrics(self, fred_provider, health_monitor):
        url_pattern = re.compile(r'https://api\.stlouisfed\.org/fred/series/observations.*')

        with aioresponses() as m:
            m.get(
                url_pattern,
                payload={"count": 0, "observations": []},
                status=200,
            )

            async with aiohttp.ClientSession() as session:
                await fred_provider.get(session, "series", series_id="GDP")

        metrics = health_monitor.get_provider_metrics("fred")
        assert metrics.total_requests == 1
        assert metrics.successful_requests == 1


@pytest.mark.unit
class TestCreateFREDProvider:
    """Tests for the create_fred_provider convenience function."""

    def test_create_provider(self, temp_cache_dir):
        provider = create_fred_provider(
            api_key="test_key",
            cache_dir=str(temp_cache_dir),
            timeout=60.0,
        )

        assert provider.provider_name == "fred"
        assert provider.api_key == "test_key"
        assert provider.config.timeout == 60.0
        assert provider.config.max_concurrency == 1  # FRED is rate-limited

    def test_create_provider_default_cache(self):
        provider = create_fred_provider(api_key="test_key")
        assert provider.provider_name == "fred"
