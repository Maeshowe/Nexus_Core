"""
Unit tests for the FMP provider.
"""

from unittest.mock import AsyncMock

import pytest

import aiohttp
from aioresponses import aioresponses

from data_loader.cache import CacheManager
from data_loader.config import ProviderConfig
from data_loader.health import HealthMonitor
from data_loader.http_client import HttpClient, RateLimitError
from data_loader.providers.fmp import FMPProvider, create_fmp_provider


@pytest.fixture
def fmp_config():
    return ProviderConfig(
        api_key="test_fmp_key",
        base_url="https://financialmodelingprep.com",
        max_concurrency=3,
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
def fmp_provider(fmp_config, http_client, cache_manager, health_monitor):
    return FMPProvider(
        config=fmp_config,
        http_client=http_client,
        cache=cache_manager,
        health_monitor=health_monitor,
    )


@pytest.mark.unit
class TestFMPProvider:
    """Tests for FMPProvider class."""

    def test_provider_name(self, fmp_provider):
        assert fmp_provider.provider_name == "fmp"

    def test_supported_endpoints(self, fmp_provider):
        endpoints = fmp_provider.get_supported_endpoints()
        assert len(endpoints) == 13
        assert "profile" in endpoints
        assert "quote" in endpoints
        assert "historical_price" in endpoints
        assert "earnings_calendar" in endpoints
        assert "balance_sheet" in endpoints
        assert "income_statement" in endpoints
        assert "cash_flow" in endpoints
        assert "ratios" in endpoints
        assert "growth" in endpoints
        assert "key_metrics" in endpoints
        assert "insider_trading" in endpoints
        assert "institutional_ownership" in endpoints
        assert "screener" in endpoints

    def test_build_url_profile(self, fmp_provider):
        url = fmp_provider._build_url("profile", symbol="AAPL")
        assert url == "https://financialmodelingprep.com/stable/profile"

    def test_build_url_quote(self, fmp_provider):
        url = fmp_provider._build_url("quote", symbol="MSFT")
        assert url == "https://financialmodelingprep.com/stable/quote"

    def test_build_url_historical_price(self, fmp_provider):
        url = fmp_provider._build_url("historical_price", symbol="GOOGL")
        assert url == "https://financialmodelingprep.com/stable/historical-price-eod/full"

    def test_build_url_earnings_calendar(self, fmp_provider):
        url = fmp_provider._build_url("earnings_calendar")
        assert url == "https://financialmodelingprep.com/stable/earnings-calendar"

    def test_build_url_insider_trading(self, fmp_provider):
        url = fmp_provider._build_url("insider_trading")
        assert url == "https://financialmodelingprep.com/stable/insider-trading/search"

    def test_build_url_screener(self, fmp_provider):
        """New stable API endpoints don't use path params for symbol."""
        url = fmp_provider._build_url("screener")
        assert url == "https://financialmodelingprep.com/stable/company-screener"

    def test_build_url_unknown_endpoint(self, fmp_provider):
        with pytest.raises(ValueError, match="Unknown endpoint"):
            fmp_provider._build_url("unknown_endpoint")

    def test_build_params_includes_api_key(self, fmp_provider):
        params = fmp_provider._build_params("profile")
        assert "apikey" in params
        assert params["apikey"] == "test_fmp_key"

    def test_build_params_filters_allowed(self, fmp_provider):
        params = fmp_provider._build_params(
            "historical_price",
            symbol="AAPL",  # Now a query param in new stable API
            **{"from": "2024-01-01", "to": "2024-01-31", "invalid": "ignored"}
        )
        assert "from" in params
        assert "to" in params
        assert "invalid" not in params
        assert "symbol" in params  # symbol is now a query param in stable API

    def test_build_params_screener(self, fmp_provider):
        params = fmp_provider._build_params(
            "screener",
            marketCapMoreThan=1000000000,
            sector="Technology",
            limit=100,
        )
        assert params["marketCapMoreThan"] == 1000000000
        assert params["sector"] == "Technology"
        assert params["limit"] == 100

    def test_cache_key_simple(self, fmp_provider):
        key = fmp_provider.cache_key("profile", symbol="AAPL")
        assert "profile" in key
        assert "symbol=AAPL" in key
        assert "apikey" not in key

    def test_cache_key_with_params(self, fmp_provider):
        key = fmp_provider.cache_key(
            "historical_price",
            symbol="AAPL",
            **{"from": "2024-01-01", "to": "2024-01-31"}
        )
        assert "historical_price" in key
        assert "symbol=AAPL" in key
        assert "from=2024-01-01" in key
        assert "to=2024-01-31" in key

    def test_validate_symbol_valid(self, fmp_provider):
        assert fmp_provider.validate_symbol("AAPL") is True
        assert fmp_provider.validate_symbol("MSFT") is True
        assert fmp_provider.validate_symbol("BRK.A") is True
        assert fmp_provider.validate_symbol("BRK-B") is True

    def test_validate_symbol_invalid(self, fmp_provider):
        assert fmp_provider.validate_symbol("") is False
        assert fmp_provider.validate_symbol(None) is False
        assert fmp_provider.validate_symbol("TOOLONGSYMBOL") is False
        assert fmp_provider.validate_symbol("INVALID!") is False


@pytest.mark.unit
class TestFMPProviderNormalize:
    """Tests for FMP response normalization."""

    def test_normalize_profile_list(self, fmp_provider):
        # Profile returns a list with single item
        data = [{"symbol": "AAPL", "companyName": "Apple Inc."}]
        result = fmp_provider.normalize(data, "profile")
        assert result == {"symbol": "AAPL", "companyName": "Apple Inc."}

    def test_normalize_quote_list(self, fmp_provider):
        # Quote returns a list with single item
        data = [{"symbol": "AAPL", "price": 185.50}]
        result = fmp_provider.normalize(data, "quote")
        assert result == {"symbol": "AAPL", "price": 185.50}

    def test_normalize_historical_price(self, fmp_provider):
        data = {
            "symbol": "AAPL",
            "historical": [
                {"date": "2024-01-02", "close": 185.50},
                {"date": "2024-01-03", "close": 186.00},
            ]
        }
        result = fmp_provider.normalize(data, "historical_price")
        assert result["symbol"] == "AAPL"
        assert len(result["historical"]) == 2

    def test_normalize_error_response(self, fmp_provider):
        data = {"Error Message": "Invalid API key"}
        result = fmp_provider.normalize(data, "profile")
        assert result["error"] == "Invalid API key"
        assert result["data"] is None

    def test_normalize_list_response(self, fmp_provider):
        # Most endpoints return lists
        data = [
            {"date": "2024-01-01", "revenue": 1000000},
            {"date": "2023-10-01", "revenue": 950000},
        ]
        result = fmp_provider.normalize(data, "income_statement")
        assert result == data  # Should return as-is


@pytest.mark.unit
class TestFMPProviderFetch:
    """Tests for FMP API fetching."""

    @pytest.mark.asyncio
    async def test_fetch_profile_success(self, fmp_provider):
        import re
        # Match URL with any query params (apikey, symbol will be added)
        url_pattern = re.compile(r'https://financialmodelingprep\.com/stable/profile\?.*')

        with aioresponses() as m:
            m.get(
                url_pattern,
                payload=[{"symbol": "AAPL", "companyName": "Apple Inc."}],
                status=200,
            )

            async with aiohttp.ClientSession() as session:
                response = await fmp_provider.fetch(session, "profile", symbol="AAPL")

            assert response.status == 200
            assert response.data == [{"symbol": "AAPL", "companyName": "Apple Inc."}]

    @pytest.mark.asyncio
    async def test_fetch_invalid_endpoint(self, fmp_provider):
        async with aiohttp.ClientSession() as session:
            with pytest.raises(ValueError, match="Invalid endpoint"):
                await fmp_provider.fetch(session, "invalid_endpoint")

    @pytest.mark.asyncio
    async def test_fetch_without_symbol_still_builds_url(self, fmp_provider):
        """In the new stable API, symbol is a query param, not a path param.

        The URL can be built without symbol - API would return empty/error.
        This test verifies the URL is built correctly without symbol param.
        """
        import re
        # Even without symbol, the URL should be built - API may return empty result
        url_pattern = re.compile(r'https://financialmodelingprep\.com/stable/profile\?.*')

        with aioresponses() as m:
            m.get(
                url_pattern,
                payload=[],  # Empty result when no symbol
                status=200,
            )

            async with aiohttp.ClientSession() as session:
                response = await fmp_provider.fetch(session, "profile")

            assert response.status == 200


@pytest.mark.unit
class TestFMPProviderIntegration:
    """Integration tests for FMP provider get method."""

    @pytest.mark.asyncio
    async def test_get_profile_success(self, fmp_provider):
        import re
        url_pattern = re.compile(r'https://financialmodelingprep\.com/stable/profile\?.*')

        with aioresponses() as m:
            m.get(
                url_pattern,
                payload=[{
                    "symbol": "AAPL",
                    "companyName": "Apple Inc.",
                    "industry": "Consumer Electronics",
                }],
                status=200,
            )

            async with aiohttp.ClientSession() as session:
                response = await fmp_provider.get(session, "profile", symbol="AAPL")

            assert response.success is True
            assert response.data["symbol"] == "AAPL"
            assert response.from_cache is False

    @pytest.mark.asyncio
    async def test_get_from_cache(self, fmp_provider, cache_manager):
        # Pre-populate cache
        cache_manager.set("fmp", "profile_symbol=AAPL", {"symbol": "AAPL", "cached": True})

        async with aiohttp.ClientSession() as session:
            response = await fmp_provider.get(session, "profile", symbol="AAPL")

        assert response.success is True
        assert response.data["cached"] is True
        assert response.from_cache is True

    @pytest.mark.asyncio
    async def test_get_caches_result(self, fmp_provider, cache_manager):
        import re
        url_pattern = re.compile(r'https://financialmodelingprep\.com/stable/profile\?.*')

        with aioresponses() as m:
            m.get(url_pattern, payload=[{"symbol": "MSFT"}], status=200)

            async with aiohttp.ClientSession() as session:
                await fmp_provider.get(session, "profile", symbol="MSFT")

        # Check cache was populated
        cached = cache_manager.get("fmp", "profile_symbol=MSFT")
        assert cached is not None
        assert cached.data["symbol"] == "MSFT"

    @pytest.mark.asyncio
    async def test_get_records_health_metrics(self, fmp_provider, health_monitor):
        import re
        url_pattern = re.compile(r'https://financialmodelingprep\.com/stable/profile\?.*')

        with aioresponses() as m:
            m.get(url_pattern, payload=[{"symbol": "GOOGL"}], status=200)

            async with aiohttp.ClientSession() as session:
                await fmp_provider.get(session, "profile", symbol="GOOGL")

        metrics = health_monitor.get_provider_metrics("fmp")
        assert metrics.total_requests == 1
        assert metrics.successful_requests == 1


@pytest.mark.unit
class TestCreateFMPProvider:
    """Tests for the create_fmp_provider convenience function."""

    def test_create_provider(self, temp_cache_dir):
        provider = create_fmp_provider(
            api_key="test_key",
            cache_dir=str(temp_cache_dir),
            timeout=60.0,
        )

        assert provider.provider_name == "fmp"
        assert provider.api_key == "test_key"
        assert provider.config.timeout == 60.0

    def test_create_provider_default_cache(self):
        provider = create_fmp_provider(api_key="test_key")
        assert provider.provider_name == "fmp"
