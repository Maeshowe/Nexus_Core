#!/usr/bin/env python3
"""
Multi-Provider Analysis Example - OmniData Nexus Core

Demonstrates fetching data from all three providers (FMP, Polygon, FRED)
and combining them for comprehensive analysis.

Usage:
    python examples/02_multi_provider_analysis.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import aiohttp

from data_loader import DataLoader


async def analyze_stock_with_context(symbol: str):
    """
    Comprehensive stock analysis combining:
    - Company fundamentals (FMP)
    - Market data (Polygon)
    - Economic context (FRED)
    """
    loader = DataLoader()

    print(f"\n{'='*60}")
    print(f"  Comprehensive Analysis: {symbol}")
    print(f"{'='*60}")

    async with aiohttp.ClientSession() as session:
        # ---- COMPANY FUNDAMENTALS (FMP) ----
        print("\n[FMP] Company Fundamentals")
        print("-" * 40)

        profile = await loader.get_fmp_data(session, "profile", symbol=symbol)
        if profile.success:
            print(f"  Company: {profile.data.get('company_name', symbol)}")
            print(f"  Sector: {profile.data.get('sector')}")
            print(f"  Industry: {profile.data.get('industry')}")

        ratios = await loader.get_fmp_data(session, "ratios", symbol=symbol)
        if ratios.success:
            data = ratios.data
            if isinstance(data, list) and data:
                data = data[0]
            print(f"  P/E Ratio: {data.get('priceEarningsRatio', 'N/A')}")
            print(f"  ROE: {data.get('returnOnEquity', 'N/A')}")

        # ---- MARKET DATA (Polygon) ----
        print("\n[Polygon] Recent Market Data")
        print("-" * 40)

        aggs = await loader.get_polygon_data(
            session, "aggs_daily",
            symbol=symbol,
            start="2025-01-01",
            end="2025-01-31"
        )
        if aggs.success:
            results = aggs.data.get("results", [])
            if results:
                first = results[0]
                last = results[-1]
                change = ((last['c'] - first['c']) / first['c']) * 100
                print(f"  Period: {len(results)} trading days")
                print(f"  Start price: ${first['c']:.2f}")
                print(f"  End price: ${last['c']:.2f}")
                print(f"  Change: {change:+.2f}%")
                print(f"  Avg volume: {sum(r['v'] for r in results) / len(results):,.0f}")

        # ---- ECONOMIC CONTEXT (FRED) ----
        print("\n[FRED] Economic Context")
        print("-" * 40)

        # Unemployment
        unrate = await loader.get_fred_data(session, "series", series_id="UNRATE")
        if unrate.success:
            obs = unrate.data.get("observations", [])
            if obs:
                print(f"  Unemployment: {obs[-1]['value']}% ({obs[-1]['date']})")

        # Fed Funds Rate
        fedfunds = await loader.get_fred_data(session, "series", series_id="FEDFUNDS")
        if fedfunds.success:
            obs = fedfunds.data.get("observations", [])
            if obs:
                print(f"  Fed Funds Rate: {obs[-1]['value']}% ({obs[-1]['date']})")

        # CPI
        cpi = await loader.get_fred_data(session, "series", series_id="CPIAUCSL")
        if cpi.success:
            obs = cpi.data.get("observations", [])
            if len(obs) >= 13:
                # Calculate YoY inflation
                current = float(obs[-1]['value'])
                year_ago = float(obs[-13]['value'])
                inflation = ((current - year_ago) / year_ago) * 100
                print(f"  YoY Inflation: {inflation:.1f}%")

    print(f"\n{'='*60}")


async def main():
    """Analyze multiple stocks."""
    for symbol in ["AAPL", "MSFT", "GOOGL"]:
        await analyze_stock_with_context(symbol)


if __name__ == "__main__":
    asyncio.run(main())
