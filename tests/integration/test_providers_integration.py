"""
Integration tests for all data providers.

These tests verify that providers work correctly together with
the caching, health monitoring, and HTTP client components.
"""

import re

import aiohttp
import pytest
from aioresponses import aioresponses

from data_loader.cache import CacheManager
from data_loader.config import ProviderConfig
from data_loader.health import HealthMonitor, ProviderStatus
from data_loader.http_client import HttpClient
from data_loader.providers import (
    FMPProvider,
    FREDProvider,
    PolygonProvider,
)


@pytest.fixture
def shared_health_monitor():
    """Shared health monitor across all providers."""
    return HealthMonitor()


@pytest.fixture
def shared_cache(temp_cache_dir):
    """Shared cache manager across all providers."""
    return CacheManager(base_dir=temp_cache_dir, ttl_days=7)


@pytest.fixture
def http_client():
    return HttpClient(timeout=30.0)


@pytest.fixture
def fmp_provider(http_client, shared_cache, shared_health_monitor):
    config = ProviderConfig(
        api_key="fmp_test_key",
        base_url="https://financialmodelingprep.com",
        max_concurrency=3,
        timeout=30.0,
    )
    return FMPProvider(
        config=config,
        http_client=http_client,
        cache=shared_cache,
        health_monitor=shared_health_monitor,
    )


@pytest.fixture
def polygon_provider(http_client, shared_cache, shared_health_monitor):
    config = ProviderConfig(
        api_key="polygon_test_key",
        base_url="https://api.polygon.io",
        max_concurrency=10,
        timeout=30.0,
    )
    return PolygonProvider(
        config=config,
        http_client=http_client,
        cache=shared_cache,
        health_monitor=shared_health_monitor,
    )


@pytest.fixture
def fred_provider(http_client, shared_cache, shared_health_monitor):
    config = ProviderConfig(
        api_key="fred_test_key",
        base_url="https://api.stlouisfed.org/fred",
        max_concurrency=1,
        timeout=30.0,
    )
    return FREDProvider(
        config=config,
        http_client=http_client,
        cache=shared_cache,
        health_monitor=shared_health_monitor,
    )


@pytest.mark.integration
class TestProvidersSharedHealthMonitor:
    """Test that providers correctly share health monitoring."""

    @pytest.mark.asyncio
    async def test_all_providers_report_to_shared_monitor(
        self, fmp_provider, polygon_provider, fred_provider, shared_health_monitor
    ):
        """Verify all providers report metrics to the shared health monitor."""
        fmp_url = re.compile(r'https://financialmodelingprep\.com/stable/profile\?.*')
        polygon_url = re.compile(r'https://api\.polygon\.io/v3/trades/SPY.*')
        fred_url = re.compile(r'https://api\.stlouisfed\.org/fred/series/observations.*')

        with aioresponses() as m:
            m.get(fmp_url, payload=[{"symbol": "AAPL"}], status=200)
            m.get(polygon_url, payload={"status": "OK", "results": []}, status=200)
            m.get(fred_url, payload={"count": 0, "observations": []}, status=200)

            async with aiohttp.ClientSession() as session:
                await fmp_provider.get(session, "profile", symbol="AAPL")
                await polygon_provider.get(session, "trades", symbol="SPY")
                await fred_provider.get(session, "series", series_id="CPIAUCSL")

        # Check all providers are tracked
        report = shared_health_monitor.get_health_report()
        assert report["providers"]["fmp"]["total_requests"] == 1
        assert report["providers"]["polygon"]["total_requests"] == 1
        assert report["providers"]["fred"]["total_requests"] == 1

    @pytest.mark.asyncio
    async def test_overall_health_degrades_on_errors(
        self, fmp_provider, polygon_provider, shared_health_monitor
    ):
        """Verify overall health status reflects worst provider."""
        fmp_url = re.compile(r'https://financialmodelingprep\.com/stable/profile\?.*')
        polygon_url = re.compile(r'https://api\.polygon\.io/v3/trades/.*')

        with aioresponses() as m:
            # FMP succeeds
            for _ in range(15):
                m.get(fmp_url, payload=[{"symbol": "AAPL"}], status=200)

            # Polygon fails with high error rate
            for _ in range(10):
                m.get(polygon_url, payload={"status": "OK", "results": []}, status=200)
            for _ in range(5):
                m.get(polygon_url, status=500)

            async with aiohttp.ClientSession() as session:
                # FMP requests - all success
                for _ in range(15):
                    await fmp_provider.get(
                        session, "profile", symbol="AAPL", use_cache=False
                    )

                # Polygon requests - mixed results
                for _i in range(15):
                    await polygon_provider.get(
                        session, "trades", symbol="SPY", use_cache=False
                    )

        # Check individual statuses
        fmp_status = shared_health_monitor.get_provider_status("fmp")
        polygon_status = shared_health_monitor.get_provider_status("polygon")

        assert fmp_status == ProviderStatus.HEALTHY
        # Polygon should be degraded or unhealthy due to errors
        assert polygon_status in (ProviderStatus.DEGRADED, ProviderStatus.UNHEALTHY)


@pytest.mark.integration
class TestProvidersSharedCache:
    """Test that providers correctly use shared cache."""

    @pytest.mark.asyncio
    async def test_providers_use_separate_cache_namespaces(
        self, fmp_provider, polygon_provider, shared_cache
    ):
        """Verify providers don't interfere with each other's cache."""
        fmp_url = re.compile(r'https://financialmodelingprep\.com/stable/profile\?.*')
        polygon_url = re.compile(r'https://api\.polygon\.io/v3/trades/AAPL.*')

        with aioresponses() as m:
            m.get(fmp_url, payload=[{"symbol": "AAPL", "source": "fmp"}], status=200)
            m.get(polygon_url, payload={"status": "OK", "results": [{"source": "polygon"}]}, status=200)

            async with aiohttp.ClientSession() as session:
                fmp_response = await fmp_provider.get(session, "profile", symbol="AAPL")
                polygon_response = await polygon_provider.get(session, "trades", symbol="AAPL")

        # Check data is different despite same symbol
        assert fmp_response.data["source"] == "fmp"
        assert polygon_response.data["results"][0]["source"] == "polygon"

        # Check cache has both entries
        stats = shared_cache.get_stats()
        assert stats["providers"]["fmp"]["total_entries"] == 1
        assert stats["providers"]["polygon"]["total_entries"] == 1

    @pytest.mark.asyncio
    async def test_cache_hit_prevents_api_call(
        self, fmp_provider, shared_cache
    ):
        """Verify cached data is returned without API call."""
        # Pre-populate cache
        shared_cache.set("fmp", "profile_symbol=MSFT", {"symbol": "MSFT", "cached": True})

        async with aiohttp.ClientSession() as session:
            response = await fmp_provider.get(session, "profile", symbol="MSFT")

        assert response.success is True
        assert response.from_cache is True
        assert response.data["cached"] is True


@pytest.mark.integration
class TestMultiProviderWorkflow:
    """Test realistic multi-provider data fetching workflows."""

    @pytest.mark.asyncio
    async def test_fetch_company_with_macro_context(
        self, fmp_provider, fred_provider, shared_health_monitor
    ):
        """Simulate fetching company data with macroeconomic context."""
        fmp_profile_url = re.compile(r'https://financialmodelingprep\.com/stable/profile\?.*')
        fmp_quote_url = re.compile(r'https://financialmodelingprep\.com/stable/quote\?.*')
        fred_cpi_url = re.compile(r'https://api\.stlouisfed\.org/fred/series/observations.*series_id=CPIAUCSL.*')
        fred_rate_url = re.compile(r'https://api\.stlouisfed\.org/fred/series/observations.*series_id=FEDFUNDS.*')

        with aioresponses() as m:
            # FMP responses
            m.get(fmp_profile_url, payload=[{
                "symbol": "AAPL",
                "companyName": "Apple Inc.",
                "sector": "Technology",
            }], status=200)
            m.get(fmp_quote_url, payload=[{
                "symbol": "AAPL",
                "price": 185.50,
                "changesPercentage": 1.2,
            }], status=200)

            # FRED responses
            m.get(fred_cpi_url, payload={
                "count": 1,
                "observations": [{"date": "2024-01-01", "value": "308.417"}]
            }, status=200)
            m.get(fred_rate_url, payload={
                "count": 1,
                "observations": [{"date": "2024-01-01", "value": "5.33"}]
            }, status=200)

            async with aiohttp.ClientSession() as session:
                # Fetch company data
                profile = await fmp_provider.get(session, "profile", symbol="AAPL")
                quote = await fmp_provider.get(session, "quote", symbol="AAPL")

                # Fetch macro context
                cpi = await fred_provider.get(session, "series", series_id="CPIAUCSL")
                fed_funds = await fred_provider.get(session, "series", series_id="FEDFUNDS")

        # All requests should succeed
        assert profile.success and profile.data["symbol"] == "AAPL"
        assert quote.success and quote.data["price"] == 185.50
        assert cpi.success and len(cpi.data["observations"]) == 1
        assert fed_funds.success and len(fed_funds.data["observations"]) == 1

        # Health monitor should track all requests
        report = shared_health_monitor.get_health_report()
        assert report["providers"]["fmp"]["total_requests"] == 2
        assert report["providers"]["fred"]["total_requests"] == 2

    @pytest.mark.asyncio
    async def test_parallel_provider_requests(
        self, fmp_provider, polygon_provider, fred_provider
    ):
        """Test concurrent requests to multiple providers."""
        import asyncio

        fmp_url = re.compile(r'https://financialmodelingprep\.com/stable/profile\?.*')
        polygon_url = re.compile(r'https://api\.polygon\.io/v2/aggs/ticker/SPY/range/.*')
        fred_url = re.compile(r'https://api\.stlouisfed\.org/fred/series/observations.*')

        with aioresponses() as m:
            m.get(fmp_url, payload=[{"symbol": "AAPL"}], status=200)
            m.get(polygon_url, payload={"ticker": "SPY", "results": []}, status=200)
            m.get(fred_url, payload={"count": 0, "observations": []}, status=200)

            async with aiohttp.ClientSession() as session:
                # Execute requests concurrently
                results = await asyncio.gather(
                    fmp_provider.get(session, "profile", symbol="AAPL"),
                    polygon_provider.get(
                        session, "aggs_daily",
                        symbol="SPY", start="2024-01-01", end="2024-01-31"
                    ),
                    fred_provider.get(session, "series", series_id="GDP"),
                )

        # All should succeed
        assert all(r.success for r in results)
        assert results[0].provider == "fmp"
        assert results[1].provider == "polygon"
        assert results[2].provider == "fred"


@pytest.mark.integration
class TestProviderErrorRecovery:
    """Test error handling and recovery across providers."""

    @pytest.mark.asyncio
    async def test_one_provider_failure_doesnt_affect_others(
        self, fmp_provider, polygon_provider, shared_health_monitor
    ):
        """Verify one provider's failure doesn't impact others."""
        fmp_url = re.compile(r'https://financialmodelingprep\.com/stable/profile\?.*')
        polygon_url = re.compile(r'https://api\.polygon\.io/v3/trades/.*')

        with aioresponses() as m:
            # FMP fails
            m.get(fmp_url, status=500)
            # Polygon succeeds
            m.get(polygon_url, payload={"status": "OK", "results": []}, status=200)

            async with aiohttp.ClientSession() as session:
                fmp_result = await fmp_provider.get(session, "profile", symbol="AAPL")
                polygon_result = await polygon_provider.get(session, "trades", symbol="SPY")

        assert fmp_result.success is False
        assert polygon_result.success is True

        # Check individual provider health
        fmp_metrics = shared_health_monitor.get_provider_metrics("fmp")
        polygon_metrics = shared_health_monitor.get_provider_metrics("polygon")

        assert fmp_metrics.failed_requests == 1
        assert polygon_metrics.successful_requests == 1

    @pytest.mark.asyncio
    async def test_rate_limit_recorded_correctly(
        self, fmp_provider, shared_health_monitor
    ):
        """Verify rate limit errors are tracked separately."""
        fmp_url = re.compile(r'https://financialmodelingprep\.com/stable/profile\?.*')

        with aioresponses() as m:
            m.get(fmp_url, status=429, headers={"Retry-After": "60"})

            async with aiohttp.ClientSession() as session:
                result = await fmp_provider.get(session, "profile", symbol="AAPL")

        assert result.success is False
        assert "Rate limit" in result.error

        metrics = shared_health_monitor.get_provider_metrics("fmp")
        assert metrics.rate_limited_requests == 1
