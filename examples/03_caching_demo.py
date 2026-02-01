#!/usr/bin/env python3
"""
Caching Demo - OmniData Nexus Core

Demonstrates the intelligent caching system:
- Automatic caching of API responses
- Cache hit detection
- Cache bypass for fresh data

Usage:
    python examples/03_caching_demo.py
"""

import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import aiohttp
from data_loader import DataLoader


async def main():
    """Demonstrate caching behavior."""
    loader = DataLoader()

    print("\n" + "=" * 50)
    print("  Caching Demonstration")
    print("=" * 50)

    async with aiohttp.ClientSession() as session:
        # First request - will fetch from API (or cache if already cached)
        print("\n[1] First request for NVDA profile...")
        start = time.perf_counter()
        result1 = await loader.get_fmp_data(session, "profile", symbol="NVDA")
        elapsed1 = (time.perf_counter() - start) * 1000

        print(f"    From cache: {result1.from_cache}")
        print(f"    Time: {elapsed1:.1f}ms")
        print(f"    Data available: {result1.success}")

        # Second request - should be instant from cache
        print("\n[2] Second request for same data...")
        start = time.perf_counter()
        result2 = await loader.get_fmp_data(session, "profile", symbol="NVDA")
        elapsed2 = (time.perf_counter() - start) * 1000

        print(f"    From cache: {result2.from_cache}")
        print(f"    Time: {elapsed2:.1f}ms")
        print(f"    Speedup: {elapsed1 / max(elapsed2, 0.1):.1f}x faster")

        # Different symbol - cache miss
        print("\n[3] Request for different symbol (AMD)...")
        result3 = await loader.get_fmp_data(session, "profile", symbol="AMD")
        print(f"    From cache: {result3.from_cache}")

        # Force bypass cache (use_cache=False)
        print("\n[4] Force fresh data (bypass cache)...")
        result4 = await loader.get_fmp_data(
            session, "profile", symbol="NVDA", use_cache=False
        )
        print(f"    From cache: {result4.from_cache}")
        print(f"    Fresh API call made: {not result4.from_cache}")

    # Show cache statistics
    print("\n" + "-" * 50)
    print("Cache Statistics:")
    report = loader.get_api_health_report()
    stats = report.get("loader_stats", {})
    print(f"  Total requests: {stats.get('total_requests', 0)}")
    print(f"  Cache hits: {stats.get('cache_hits', 0)}")
    print(f"  API calls: {stats.get('api_calls', 0)}")
    print(f"  Cache hit rate: {stats.get('cache_hit_rate', 0):.1%}")


if __name__ == "__main__":
    asyncio.run(main())
