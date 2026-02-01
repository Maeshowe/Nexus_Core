#!/usr/bin/env python3
"""
Error Handling Demo - OmniData Nexus Core

Demonstrates resilience features:
- Graceful error handling
- Circuit breaker status
- Health monitoring
- Fallback strategies

Usage:
    python examples/04_error_handling.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import aiohttp

from data_loader import DataLoader, ReadOnlyError


async def fetch_with_fallback(loader, session, symbol: str) -> dict:
    """
    Fetch data with graceful fallback handling.

    Returns:
        dict with data and metadata about the fetch
    """
    result = {
        "symbol": symbol,
        "data": None,
        "source": None,
        "error": None,
    }

    try:
        # Try to fetch fresh data
        response = await loader.get_fmp_data(session, "profile", symbol=symbol)

        if response.success:
            result["data"] = response.data
            result["source"] = "cache" if response.from_cache else "api"
        else:
            result["error"] = response.error

    except ReadOnlyError as e:
        result["error"] = f"READ_ONLY mode: {e}"
        result["source"] = "none"

    except Exception as e:
        result["error"] = str(e)
        result["source"] = "error"

    return result


async def main():
    """Demonstrate error handling patterns."""
    loader = DataLoader()

    print("\n" + "=" * 50)
    print("  Error Handling Demonstration")
    print("=" * 50)

    async with aiohttp.ClientSession() as session:
        # Normal fetch
        print("\n[1] Normal fetch (should succeed)...")
        result = await fetch_with_fallback(loader, session, "AAPL")
        print(f"    Symbol: {result['symbol']}")
        print(f"    Source: {result['source']}")
        print(f"    Error: {result['error']}")
        print(f"    Has data: {result['data'] is not None}")

        # Fetch with invalid symbol (graceful handling)
        print("\n[2] Fetch with potentially invalid symbol...")
        result = await fetch_with_fallback(loader, session, "INVALID_SYMBOL_XYZ")
        print(f"    Symbol: {result['symbol']}")
        print(f"    Source: {result['source']}")
        print(f"    Error: {result['error']}")

    # Health report shows system status
    print("\n" + "-" * 50)
    print("Health Report:")
    report = loader.get_api_health_report()

    print(f"  Operating Mode: {report.get('operating_mode')}")
    print(f"  Overall Status: {report.get('overall_status')}")

    # Circuit breaker status
    cb_status = report.get("circuit_breakers", {})
    print("\n  Circuit Breakers:")
    for provider, status in cb_status.items():
        state = status.get("state", "UNKNOWN")
        failures = status.get("failure_count", status.get("failures", 0))
        print(f"    {provider}: {state} (failures: {failures})")

    # Provider status
    providers = report.get("providers", {})
    print("\n  Provider Status:")
    for provider, status in providers.items():
        print(f"    {provider}: {status.get('status', 'UNKNOWN')}")


if __name__ == "__main__":
    asyncio.run(main())
