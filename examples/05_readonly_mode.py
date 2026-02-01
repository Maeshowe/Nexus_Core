#!/usr/bin/env python3
"""
READ_ONLY Mode Demo - OmniData Nexus Core

Demonstrates READ_ONLY mode for offline analysis:
- No API calls made
- Only cached data served
- Useful for offline analysis, testing, or rate limit protection

Usage:
    python examples/05_readonly_mode.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import aiohttp
from data_loader import DataLoader, OperatingMode, ReadOnlyError


async def main():
    """Demonstrate READ_ONLY mode."""
    loader = DataLoader()

    print("\n" + "=" * 50)
    print("  READ_ONLY Mode Demonstration")
    print("=" * 50)

    async with aiohttp.ClientSession() as session:
        # First, fetch some data in LIVE mode to populate cache
        print("\n[1] LIVE mode: Populating cache...")
        print(f"    Current mode: {loader.get_operating_mode()}")

        response = await loader.get_fmp_data(session, "profile", symbol="TSLA")
        print(f"    Fetched TSLA: {response.success}")
        print(f"    From cache: {response.from_cache}")

        # Switch to READ_ONLY mode
        print("\n[2] Switching to READ_ONLY mode...")
        loader.set_operating_mode(OperatingMode.READ_ONLY)
        print(f"    Current mode: {loader.get_operating_mode()}")

        # Try to fetch cached data (should succeed)
        print("\n[3] READ_ONLY: Fetching cached data (TSLA)...")
        try:
            response = await loader.get_fmp_data(session, "profile", symbol="TSLA")
            print(f"    Success: {response.success}")
            print(f"    From cache: {response.from_cache}")
            print(f"    Data available: {response.data is not None}")
        except ReadOnlyError as e:
            print(f"    Error: {e}")

        # Try to fetch uncached data (should fail gracefully)
        print("\n[4] READ_ONLY: Fetching uncached data (UNUSUAL_SYMBOL)...")
        try:
            response = await loader.get_fmp_data(
                session, "profile", symbol="UNUSUAL_SYMBOL_12345"
            )
            if response.success:
                print(f"    Unexpectedly succeeded!")
            else:
                print(f"    Failed as expected: {response.error}")
        except ReadOnlyError as e:
            print(f"    ReadOnlyError (expected): Data not in cache")

        # Switch back to LIVE mode
        print("\n[5] Switching back to LIVE mode...")
        loader.set_operating_mode(OperatingMode.LIVE)
        print(f"    Current mode: {loader.get_operating_mode()}")

    print("\n" + "-" * 50)
    print("Use cases for READ_ONLY mode:")
    print("  - Offline data analysis")
    print("  - Testing without API calls")
    print("  - Rate limit protection")
    print("  - Reproducible analysis with cached data")


if __name__ == "__main__":
    asyncio.run(main())
