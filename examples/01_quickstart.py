#!/usr/bin/env python3
"""
Quick Start Example - OmniData Nexus Core

Demonstrates basic usage of the DataLoader to fetch financial data
from multiple providers (FMP, Polygon, FRED).

Requirements:
    - .env file with API keys (FMP_KEY, POLYGON_KEY, FRED_KEY)
    - pip install omnidata-nexus-core (or run from source with PYTHONPATH=src)

Usage:
    python examples/01_quickstart.py
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import aiohttp
from data_loader import DataLoader


async def main():
    """Fetch basic company and economic data."""
    loader = DataLoader()

    async with aiohttp.ClientSession() as session:
        # 1. Fetch company profile from FMP
        print("Fetching Apple profile...")
        profile = await loader.get_fmp_data(session, "profile", symbol="AAPL")

        if profile.success:
            print(f"  Company: {profile.data.get('company_name', 'Apple Inc.')}")
            print(f"  Sector: {profile.data.get('sector')}")
            print(f"  Market Cap: ${profile.data.get('market_cap', 0):,.0f}")

        # 2. Fetch real-time quote from FMP
        print("\nFetching Microsoft quote...")
        quote = await loader.get_fmp_data(session, "quote", symbol="MSFT")

        if quote.success:
            print(f"  Price: ${quote.data.get('price')}")
            print(f"  Change: {quote.data.get('change_percent', 0):.2f}%")

        # 3. Fetch macroeconomic data from FRED
        print("\nFetching unemployment rate...")
        unemployment = await loader.get_fred_data(session, "series", series_id="UNRATE")

        if unemployment.success:
            observations = unemployment.data.get("observations", [])
            if observations:
                latest = observations[-1]
                print(f"  Latest ({latest['date']}): {latest['value']}%")

        # 4. Check health report
        print("\nHealth Report:")
        report = loader.get_api_health_report()
        stats = report.get("loader_stats", {})
        print(f"  Total requests: {stats.get('total_requests', 0)}")
        print(f"  Cache hits: {stats.get('cache_hits', 0)}")


if __name__ == "__main__":
    asyncio.run(main())
