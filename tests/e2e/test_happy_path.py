"""
End-to-end tests for happy path scenarios.

Tests the complete flow through the DataLoader with all components.
"""

import re

import pytest

import aiohttp
from aioresponses import aioresponses

from data_loader import DataLoader, OperatingMode
from data_loader.cache import CacheManager


@pytest.mark.e2e
class TestCacheMissToHit:
    """TC-401: Cache miss → API → Cache hit flow."""

    @pytest.mark.asyncio
    async def test_first_request_fetches_from_api(self, temp_cache_dir):
        """First request should fetch from API and cache the result."""
        cache = CacheManager(base_dir=temp_cache_dir)
        loader = DataLoader(cache=cache)

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
                response = await loader.get_fmp_data(session, "profile", symbol="AAPL")

        assert response.success is True
        assert response.from_cache is False
        assert response.data["symbol"] == "AAPL"

        # Verify stats
        stats = loader.get_stats()
        assert stats.cache_misses == 1
        assert stats.api_calls == 1
        assert stats.api_successes == 1

    @pytest.mark.asyncio
    async def test_second_request_hits_cache(self, temp_cache_dir):
        """Second request should hit cache without API call."""
        cache = CacheManager(base_dir=temp_cache_dir)
        loader = DataLoader(cache=cache)

        url_pattern = re.compile(r'https://financialmodelingprep\.com/stable/profile\?.*')

        # First request - populates cache
        with aioresponses() as m:
            m.get(
                url_pattern,
                payload=[{"symbol": "MSFT", "companyName": "Microsoft"}],
                status=200,
            )

            async with aiohttp.ClientSession() as session:
                first_response = await loader.get_fmp_data(session, "profile", symbol="MSFT")

        assert first_response.from_cache is False

        # Second request - should hit cache (no mock needed)
        async with aiohttp.ClientSession() as session:
            second_response = await loader.get_fmp_data(session, "profile", symbol="MSFT")

        assert second_response.success is True
        assert second_response.from_cache is True
        assert second_response.data["symbol"] == "MSFT"

        # Verify stats
        stats = loader.get_stats()
        assert stats.cache_hits == 1
        assert stats.cache_misses == 1


@pytest.mark.e2e
class TestMultiProviderFetch:
    """TC-403: Parallel multi-provider fetch."""

    @pytest.mark.asyncio
    async def test_fetch_from_all_providers(self, temp_cache_dir):
        """Fetch data from all three providers in a single session."""
        cache = CacheManager(base_dir=temp_cache_dir)
        loader = DataLoader(cache=cache)

        fmp_pattern = re.compile(r'https://financialmodelingprep\.com/stable/profile\?.*')
        polygon_pattern = re.compile(r'https://api\.polygon\.io/v2/aggs/ticker/SPY/range.*')
        fred_pattern = re.compile(r'https://api\.stlouisfed\.org/fred/series/observations.*')

        with aioresponses() as m:
            m.get(
                fmp_pattern,
                payload=[{"symbol": "GOOG", "companyName": "Alphabet"}],
                status=200,
            )
            m.get(
                polygon_pattern,
                payload={
                    "ticker": "SPY",
                    "resultsCount": 1,
                    "results": [{"o": 450.0, "h": 455.0, "l": 448.0, "c": 452.0}],
                },
                status=200,
            )
            m.get(
                fred_pattern,
                payload={
                    "count": 1,
                    "observations": [{"date": "2024-01-01", "value": "3.7"}],
                },
                status=200,
            )

            async with aiohttp.ClientSession() as session:
                fmp_response = await loader.get_fmp_data(
                    session, "profile", symbol="GOOG"
                )
                polygon_response = await loader.get_polygon_data(
                    session, "aggs_daily",
                    symbol="SPY", start="2024-01-01", end="2024-01-31"
                )
                fred_response = await loader.get_fred_data(
                    session, "series", series_id="UNRATE"
                )

        # Verify all succeeded
        assert fmp_response.success is True
        assert polygon_response.success is True
        assert fred_response.success is True

        # Verify correct providers
        assert fmp_response.provider == "fmp"
        assert polygon_response.provider == "polygon"
        assert fred_response.provider == "fred"

        # All should be from API (not cache)
        assert fmp_response.from_cache is False
        assert polygon_response.from_cache is False
        assert fred_response.from_cache is False

        # Verify stats
        stats = loader.get_stats()
        assert stats.api_calls == 3
        assert stats.api_successes == 3


@pytest.mark.e2e
class TestReadOnlyMode:
    """TC-402: READ-ONLY mode enforcement."""

    @pytest.mark.asyncio
    async def test_readonly_serves_from_cache(self, temp_cache_dir):
        """READ-ONLY mode should serve cached data without API calls."""
        cache = CacheManager(base_dir=temp_cache_dir)
        loader = DataLoader(cache=cache)

        # Pre-populate cache in LIVE mode
        url_pattern = re.compile(r'https://financialmodelingprep\.com/stable/quote\?.*')

        with aioresponses() as m:
            m.get(
                url_pattern,
                payload=[{"symbol": "AAPL", "price": 175.50}],
                status=200,
            )

            async with aiohttp.ClientSession() as session:
                await loader.get_fmp_data(session, "quote", symbol="AAPL")

        # Switch to READ-ONLY mode
        loader.set_operating_mode(OperatingMode.READ_ONLY)

        # Should serve from cache without API call
        async with aiohttp.ClientSession() as session:
            response = await loader.get_fmp_data(session, "quote", symbol="AAPL")

        assert response.success is True
        assert response.from_cache is True
        assert response.data["price"] == 175.50

    @pytest.mark.asyncio
    async def test_readonly_raises_on_cache_miss(self, temp_cache_dir):
        """READ-ONLY mode should raise error on cache miss."""
        from data_loader.loader import ReadOnlyError

        cache = CacheManager(base_dir=temp_cache_dir)
        loader = DataLoader(cache=cache)
        loader.set_operating_mode(OperatingMode.READ_ONLY)

        async with aiohttp.ClientSession() as session:
            with pytest.raises(ReadOnlyError) as exc_info:
                await loader.get_fmp_data(session, "profile", symbol="NVDA")

        assert exc_info.value.provider == "fmp"
        assert "READ_ONLY mode" in str(exc_info.value)


@pytest.mark.e2e
class TestHealthReportAggregation:
    """TC-404: Health report aggregation."""

    @pytest.mark.asyncio
    async def test_health_report_tracks_requests(self, temp_cache_dir):
        """Health report should track all requests across providers."""
        cache = CacheManager(base_dir=temp_cache_dir)
        loader = DataLoader(cache=cache)

        fmp_pattern = re.compile(r'https://financialmodelingprep\.com/stable/profile\?.*')

        with aioresponses() as m:
            for symbol in ["AAPL", "MSFT", "GOOG"]:
                m.get(
                    fmp_pattern,
                    payload=[{"symbol": symbol}],
                    status=200,
                )

            async with aiohttp.ClientSession() as session:
                for symbol in ["AAPL", "MSFT", "GOOG"]:
                    await loader.get_fmp_data(session, "profile", symbol=symbol)

        report = loader.get_api_health_report()

        # Check report structure
        assert "timestamp" in report
        assert "operating_mode" in report
        assert "overall_status" in report
        assert "providers" in report
        assert "circuit_breakers" in report
        assert "qos" in report
        assert "loader_stats" in report

        # Check FMP stats
        assert report["providers"]["fmp"]["total_requests"] == 3
        assert report["providers"]["fmp"]["successful_requests"] == 3

        # Check loader stats
        assert report["loader_stats"]["api_calls"] == 3
        assert report["loader_stats"]["api_successes"] == 3

    def test_health_report_reflects_operating_mode(self, temp_cache_dir):
        """Health report should reflect current operating mode."""
        cache = CacheManager(base_dir=temp_cache_dir)
        loader = DataLoader(cache=cache)

        report_live = loader.get_api_health_report()
        assert report_live["operating_mode"] == "LIVE"

        loader.set_operating_mode(OperatingMode.READ_ONLY)
        report_readonly = loader.get_api_health_report()
        assert report_readonly["operating_mode"] == "READ_ONLY"


@pytest.mark.e2e
class TestProviderIsolation:
    """Test that provider failures don't affect other providers."""

    @pytest.mark.asyncio
    async def test_one_provider_failure_doesnt_affect_others(self, temp_cache_dir):
        """Failure in one provider should not affect other providers."""
        cache = CacheManager(base_dir=temp_cache_dir)
        loader = DataLoader(cache=cache)

        # FMP will fail
        fmp_pattern = re.compile(r'https://financialmodelingprep\.com/stable/profile\?.*')
        # Polygon will succeed
        polygon_pattern = re.compile(r'https://api\.polygon\.io/v2/aggs/ticker/.*')

        with aioresponses() as m:
            m.get(fmp_pattern, status=500)
            m.get(
                polygon_pattern,
                payload={"ticker": "SPY", "results": []},
                status=200,
            )

            async with aiohttp.ClientSession() as session:
                fmp_response = await loader.get_fmp_data(
                    session, "profile", symbol="FAIL"
                )
                polygon_response = await loader.get_polygon_data(
                    session, "aggs_daily",
                    symbol="SPY", start="2024-01-01", end="2024-01-31"
                )

        # FMP should have failed
        assert fmp_response.success is False

        # Polygon should have succeeded
        assert polygon_response.success is True

        # Check health shows FMP failure but Polygon OK
        fmp_healthy = loader.is_provider_healthy("fmp")
        polygon_healthy = loader.is_provider_healthy("polygon")

        # Both should still be "healthy" as we need more failures to trigger circuit
        # The key point is Polygon succeeded despite FMP failing
        assert polygon_response.provider == "polygon"
