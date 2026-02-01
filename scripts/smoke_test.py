#!/usr/bin/env python3
"""
Smoke test script for real API validation.

Usage:
    python scripts/smoke_test.py

Requires .env file with API keys:
    FMP_KEY=...
    POLYGON_KEY=...
    FRED_KEY=...
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import aiohttp

from data_loader import DataLoader


async def test_fmp():
    """Test FMP provider with real API."""
    print("\n" + "=" * 50)
    print("🔍 Testing FMP Provider")
    print("=" * 50)

    loader = DataLoader()

    async with aiohttp.ClientSession() as session:
        # Test profile endpoint
        print("\n📊 Fetching AAPL profile...")
        response = await loader.get_fmp_data(session, "profile", symbol="AAPL")

        if response.success:
            print(f"   ✅ Success! Company: {response.data.get('company_name', 'N/A')}")
            print(f"   📈 Sector: {response.data.get('sector', 'N/A')}")
            print(f"   ⏱️  Latency: {response.latency_ms:.0f}ms")
            print(f"   💾 From cache: {response.from_cache}")
        else:
            print(f"   ❌ Failed: {response.error}")
            return False

        # Test quote endpoint
        print("\n📊 Fetching MSFT quote...")
        response = await loader.get_fmp_data(session, "quote", symbol="MSFT")

        if response.success:
            print(f"   ✅ Success! Price: ${response.data.get('price', 'N/A')}")
            print(f"   ⏱️  Latency: {response.latency_ms:.0f}ms")
        else:
            print(f"   ❌ Failed: {response.error}")
            return False

    return True


async def test_polygon():
    """Test Polygon provider with real API."""
    print("\n" + "=" * 50)
    print("🔍 Testing Polygon Provider")
    print("=" * 50)

    loader = DataLoader()

    async with aiohttp.ClientSession() as session:
        print("\n📊 Fetching SPY daily aggregates...")
        response = await loader.get_polygon_data(
            session,
            "aggs_daily",
            symbol="SPY",
            start="2024-01-01",
            end="2024-01-31"
        )

        if response.success:
            results = response.data.get("results", [])
            print(f"   ✅ Success! Got {len(results)} data points")
            print(f"   ⏱️  Latency: {response.latency_ms:.0f}ms")
            print(f"   💾 From cache: {response.from_cache}")
            if results:
                print(f"   📈 First close: ${results[0].get('c', 'N/A')}")
        else:
            print(f"   ❌ Failed: {response.error}")
            return False

    return True


async def test_fred():
    """Test FRED provider with real API."""
    print("\n" + "=" * 50)
    print("🔍 Testing FRED Provider")
    print("=" * 50)

    loader = DataLoader()

    async with aiohttp.ClientSession() as session:
        # Test unemployment rate
        print("\n📊 Fetching UNRATE (Unemployment Rate)...")
        response = await loader.get_fred_data(session, "series", series_id="UNRATE")

        if response.success:
            obs = response.data.get("observations", [])
            print(f"   ✅ Success! Got {len(obs)} observations")
            print(f"   ⏱️  Latency: {response.latency_ms:.0f}ms")
            print(f"   💾 From cache: {response.from_cache}")
            if obs:
                latest = obs[-1]
                print(f"   📈 Latest: {latest.get('date')} = {latest.get('value')}%")
        else:
            print(f"   ❌ Failed: {response.error}")
            return False

        # Test CPI
        print("\n📊 Fetching CPIAUCSL (Consumer Price Index)...")
        response = await loader.get_fred_data(session, "series", series_id="CPIAUCSL")

        if response.success:
            obs = response.data.get("observations", [])
            print(f"   ✅ Success! Got {len(obs)} observations")
            if obs:
                latest = obs[-1]
                print(f"   📈 Latest: {latest.get('date')} = {latest.get('value')}")
        else:
            print(f"   ❌ Failed: {response.error}")
            return False

    return True


async def test_cache_hit():
    """Test that second request hits cache."""
    print("\n" + "=" * 50)
    print("🔍 Testing Cache Hit")
    print("=" * 50)

    loader = DataLoader()

    async with aiohttp.ClientSession() as session:
        print("\n📊 First request (should be API call)...")
        response1 = await loader.get_fmp_data(session, "profile", symbol="GOOG")

        if not response1.success:
            print(f"   ❌ First request failed: {response1.error}")
            return False

        print(f"   From cache: {response1.from_cache}")

        print("\n📊 Second request (should be cache hit)...")
        response2 = await loader.get_fmp_data(session, "profile", symbol="GOOG")

        if response2.from_cache:
            print("   ✅ Cache hit confirmed!")
        else:
            print("   ⚠️  Expected cache hit, got API call")

    return True


async def test_health_report():
    """Test health report generation."""
    print("\n" + "=" * 50)
    print("🔍 Testing Health Report")
    print("=" * 50)

    loader = DataLoader()

    async with aiohttp.ClientSession() as session:
        # Make some requests first
        await loader.get_fmp_data(session, "quote", symbol="NVDA")

    report = loader.get_api_health_report()

    print("\n📊 Health Report:")
    print(f"   Operating Mode: {report.get('operating_mode')}")
    print(f"   Overall Status: {report.get('overall_status')}")

    stats = report.get("loader_stats", {})
    print("\n   📈 Stats:")
    print(f"      Total Requests: {stats.get('total_requests', 0)}")
    print(f"      Cache Hits: {stats.get('cache_hits', 0)}")
    print(f"      API Calls: {stats.get('api_calls', 0)}")
    print(f"      Cache Hit Rate: {stats.get('cache_hit_rate', 0):.1%}")

    return True


async def main():
    """Run all smoke tests."""
    print("\n" + "🚀" * 25)
    print("   OmniData Nexus Core - Smoke Test")
    print("🚀" * 25)

    results = {}

    try:
        results["FMP"] = await test_fmp()
    except Exception as e:
        print(f"   ❌ FMP test error: {e}")
        results["FMP"] = False

    try:
        results["Polygon"] = await test_polygon()
    except Exception as e:
        print(f"   ❌ Polygon test error: {e}")
        results["Polygon"] = False

    try:
        results["FRED"] = await test_fred()
    except Exception as e:
        print(f"   ❌ FRED test error: {e}")
        results["FRED"] = False

    try:
        results["Cache"] = await test_cache_hit()
    except Exception as e:
        print(f"   ❌ Cache test error: {e}")
        results["Cache"] = False

    try:
        results["Health"] = await test_health_report()
    except Exception as e:
        print(f"   ❌ Health test error: {e}")
        results["Health"] = False

    # Summary
    print("\n" + "=" * 50)
    print("📋 SUMMARY")
    print("=" * 50)

    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if not passed:
            all_passed = False

    print("\n" + ("🎉 All tests passed!" if all_passed else "⚠️  Some tests failed"))

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
