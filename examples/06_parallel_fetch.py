#!/usr/bin/env python3
"""
Parallel Fetch Demo - OmniData Nexus Core

Demonstrates concurrent data fetching:
- Parallel requests to multiple endpoints
- QoS limits respected automatically
- Efficient bulk data collection

Usage:
    python examples/06_parallel_fetch.py
"""

import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import aiohttp

from data_loader import DataLoader


async def fetch_portfolio_data(symbols: list[str]) -> dict:
    """
    Fetch data for multiple symbols in parallel.

    The DataLoader automatically handles:
    - Concurrent request limits (QoS)
    - Caching
    - Error handling per request
    """
    loader = DataLoader()
    results = {}

    async with aiohttp.ClientSession() as session:
        # Create tasks for parallel execution
        tasks = []
        for symbol in symbols:
            task = loader.get_fmp_data(session, "profile", symbol=symbol)
            tasks.append((symbol, task))

        # Execute all tasks concurrently
        for symbol, task in tasks:
            try:
                response = await task
                results[symbol] = {
                    "success": response.success,
                    "data": response.data if response.success else None,
                    "from_cache": response.from_cache,
                }
            except Exception as e:
                results[symbol] = {
                    "success": False,
                    "data": None,
                    "error": str(e),
                }

    return results


async def main():
    """Demonstrate parallel fetching."""
    print("\n" + "=" * 50)
    print("  Parallel Fetch Demonstration")
    print("=" * 50)

    # Portfolio of tech stocks
    portfolio = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA"]

    print(f"\nFetching data for {len(portfolio)} symbols...")
    print(f"Symbols: {', '.join(portfolio)}")

    start = time.perf_counter()
    results = await fetch_portfolio_data(portfolio)
    elapsed = time.perf_counter() - start

    print(f"\nCompleted in {elapsed:.2f} seconds")
    print("-" * 50)

    # Summary
    successful = sum(1 for r in results.values() if r.get("success"))
    from_cache = sum(1 for r in results.values() if r.get("from_cache"))

    print("\nResults:")
    for symbol, result in results.items():
        status = "OK" if result.get("success") else "FAIL"
        source = "cache" if result.get("from_cache") else "api"
        sector = "N/A"
        if result.get("data"):
            sector = result["data"].get("sector", "N/A")
        print(f"  {symbol}: {status} ({source}) - {sector}")

    print("\nSummary:")
    print(f"  Successful: {successful}/{len(portfolio)}")
    print(f"  From cache: {from_cache}/{successful}")
    print(f"  Total time: {elapsed:.2f}s")
    print(f"  Avg time per symbol: {elapsed/len(portfolio)*1000:.0f}ms")


if __name__ == "__main__":
    asyncio.run(main())
