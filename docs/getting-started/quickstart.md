# Quick Start

This guide gets you fetching financial data in under 5 minutes.

## Prerequisites

- [Installation](installation.md) complete
- [Configuration](configuration.md) with API keys

## Basic Usage

```python
import asyncio
import aiohttp
from data_loader import DataLoader

async def main():
    loader = DataLoader()

    async with aiohttp.ClientSession() as session:
        # Fetch company profile
        profile = await loader.get_fmp_data(session, "profile", symbol="AAPL")
        print(f"Company: {profile.data['companyName']}")
        print(f"Sector: {profile.data['sector']}")
        print(f"Market Cap: ${profile.data['mktCap']:,.0f}")

asyncio.run(main())
```

## Fetching from Multiple Providers

```python
async def comprehensive_analysis():
    loader = DataLoader()

    async with aiohttp.ClientSession() as session:
        # Company data (FMP)
        profile = await loader.get_fmp_data(session, "profile", symbol="AAPL")
        ratios = await loader.get_fmp_data(session, "ratios", symbol="AAPL")

        # Market data (Polygon)
        aggs = await loader.get_polygon_data(
            session, "aggs_daily",
            symbol="SPY",
            start="2025-01-01",
            end="2025-01-31"
        )

        # Economic context (FRED)
        cpi = await loader.get_fred_data(session, "series", series_id="CPIAUCSL")
        fed_rate = await loader.get_fred_data(session, "series", series_id="FEDFUNDS")

        return {
            "company": profile.data,
            "ratios": ratios.data,
            "market": aggs.data,
            "inflation": cpi.data,
            "rates": fed_rate.data,
        }
```

## Understanding the Response

Each API call returns a `DataResult` object:

```python
result = await loader.get_fmp_data(session, "profile", symbol="AAPL")

print(result.data)        # The actual data (dict or list)
print(result.from_cache)  # True if served from cache
print(result.timestamp)   # When data was fetched
print(result.provider)    # 'fmp', 'polygon', or 'fred'
```

## Caching Behavior

Data is automatically cached:

```python
async def caching_demo():
    loader = DataLoader()

    async with aiohttp.ClientSession() as session:
        # First call: API request, cached
        result1 = await loader.get_fmp_data(session, "profile", symbol="MSFT")
        print(f"From cache: {result1.from_cache}")  # False

        # Second call: served from cache
        result2 = await loader.get_fmp_data(session, "profile", symbol="MSFT")
        print(f"From cache: {result2.from_cache}")  # True

        # Force fresh data
        result3 = await loader.get_fmp_data(
            session, "profile", symbol="MSFT", use_cache=False
        )
        print(f"From cache: {result3.from_cache}")  # False
```

## Error Handling

```python
from data_loader import DataLoader
from data_loader.exceptions import (
    ProviderError,
    RateLimitError,
    ReadOnlyError,
)

async def safe_fetch():
    loader = DataLoader()

    async with aiohttp.ClientSession() as session:
        try:
            result = await loader.get_fmp_data(session, "profile", symbol="AAPL")
            return result.data
        except RateLimitError:
            print("Rate limited - waiting...")
        except ProviderError as e:
            print(f"Provider error: {e}")
        except ReadOnlyError:
            print("Data not in cache (READ_ONLY mode)")
```

## Health Monitoring

```python
async def check_status():
    loader = DataLoader()

    async with aiohttp.ClientSession() as session:
        # Make some requests
        await loader.get_fmp_data(session, "profile", symbol="AAPL")
        await loader.get_fred_data(session, "series", series_id="GDP")

    # Get health report
    report = loader.get_api_health_report()

    print(f"Mode: {report['operating_mode']}")
    print(f"Status: {report['overall_status']}")

    for provider, metrics in report['providers'].items():
        success_rate = metrics['successful_requests'] / max(metrics['total_requests'], 1)
        print(f"{provider}: {success_rate:.0%} success rate")
```

## Next Steps

- [DataLoader Guide](../guide/dataloader.md) - Detailed usage patterns
- [Providers](../guide/providers.md) - All available endpoints
- [API Reference](../api/loader.md) - Full API documentation
