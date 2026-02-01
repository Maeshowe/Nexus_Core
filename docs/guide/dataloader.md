# DataLoader Guide

The `DataLoader` class provides a unified interface for fetching data from all supported providers.

## Basic Usage

```python
import asyncio
import aiohttp
from data_loader import DataLoader

async def main():
    loader = DataLoader()

    async with aiohttp.ClientSession() as session:
        result = await loader.get_fmp_data(session, "profile", symbol="AAPL")
        print(result.data)

asyncio.run(main())
```

## Provider Methods

### FMP (Financial Modeling Prep)

```python
# Company profile
profile = await loader.get_fmp_data(session, "profile", symbol="AAPL")

# Real-time quote
quote = await loader.get_fmp_data(session, "quote", symbol="AAPL")

# Financial statements
income = await loader.get_fmp_data(session, "income_statement", symbol="AAPL", period="annual")
balance = await loader.get_fmp_data(session, "balance_sheet", symbol="AAPL", period="quarterly")
cashflow = await loader.get_fmp_data(session, "cash_flow", symbol="AAPL")

# Metrics and ratios
ratios = await loader.get_fmp_data(session, "ratios", symbol="AAPL")
growth = await loader.get_fmp_data(session, "growth", symbol="AAPL")
key_metrics = await loader.get_fmp_data(session, "key_metrics", symbol="AAPL")

# Ownership data
insider = await loader.get_fmp_data(session, "insider_trading", symbol="AAPL")
institutional = await loader.get_fmp_data(session, "institutional_ownership", symbol="AAPL")

# Calendar and screening
earnings = await loader.get_fmp_data(session, "earnings_calendar", **{"from": "2025-01-01", "to": "2025-01-31"})
screened = await loader.get_fmp_data(session, "screener", marketCapMoreThan=1000000000, sector="Technology")
```

### Polygon

```python
# Daily aggregates
aggs = await loader.get_polygon_data(
    session, "aggs_daily",
    symbol="SPY",
    start="2025-01-01",
    end="2025-01-31"
)

# Tick-level trades
trades = await loader.get_polygon_data(session, "trades", symbol="AAPL")

# Options data
options = await loader.get_polygon_data(session, "options_snapshot", underlying="AAPL")

# Market snapshot
snapshot = await loader.get_polygon_data(session, "market_snapshot")
```

### FRED

```python
# Economic series
gdp = await loader.get_fred_data(session, "series", series_id="GDP")
cpi = await loader.get_fred_data(session, "series", series_id="CPIAUCSL")
unemployment = await loader.get_fred_data(session, "series", series_id="UNRATE")
fed_funds = await loader.get_fred_data(session, "series", series_id="FEDFUNDS")
```

## DataResult Object

All provider methods return a `DataResult` object:

```python
@dataclass
class DataResult:
    data: Any           # The fetched data
    from_cache: bool    # True if served from cache
    timestamp: str      # ISO timestamp
    provider: str       # 'fmp', 'polygon', or 'fred'
    endpoint: str       # The endpoint name
```

### Accessing Data

```python
result = await loader.get_fmp_data(session, "profile", symbol="AAPL")

# Access the data
company_name = result.data['companyName']
market_cap = result.data['mktCap']

# Check if from cache
if result.from_cache:
    print("Served from cache")
```

## Caching Control

### Default Behavior

Data is automatically cached for the configured TTL (default: 7 days).

```python
# First call: fetches from API
result1 = await loader.get_fmp_data(session, "profile", symbol="AAPL")
print(result1.from_cache)  # False

# Second call: served from cache
result2 = await loader.get_fmp_data(session, "profile", symbol="AAPL")
print(result2.from_cache)  # True
```

### Bypass Cache

```python
# Force fresh data
result = await loader.get_fmp_data(
    session, "profile", symbol="AAPL", use_cache=False
)
```

### Cache Stats

```python
stats = loader._cache.get_stats()
print(f"Total entries: {stats['total_entries']}")
print(f"Total size: {stats['total_size_mb']:.2f} MB")
```

## Operating Modes

### LIVE Mode (Default)

Makes API calls when data is not cached:

```python
loader = DataLoader()  # LIVE mode by default
```

### READ_ONLY Mode

Only serves cached data, never makes API calls:

```python
from data_loader import DataLoader, OperatingMode

loader = DataLoader()
loader.set_operating_mode(OperatingMode.READ_ONLY)

try:
    result = await loader.get_fmp_data(session, "profile", symbol="AAPL")
except ReadOnlyError:
    print("Data not in cache")
```

### Checking Mode

```python
current_mode = loader.get_operating_mode()
print(f"Mode: {current_mode}")
```

## Concurrent Requests

The DataLoader manages concurrency limits per provider:

| Provider | Concurrency Limit |
|----------|-------------------|
| FMP | 3 |
| Polygon | 10 |
| FRED | 1 |

```python
# These are automatically throttled
await asyncio.gather(
    loader.get_fmp_data(session, "profile", symbol="AAPL"),
    loader.get_fmp_data(session, "profile", symbol="MSFT"),
    loader.get_fmp_data(session, "profile", symbol="GOOGL"),
    loader.get_fmp_data(session, "profile", symbol="AMZN"),  # Waits for slot
)
```

## Error Handling

```python
from data_loader.exceptions import (
    ProviderError,
    RateLimitError,
    CircuitBreakerOpenError,
    ReadOnlyError,
)

try:
    result = await loader.get_fmp_data(session, "profile", symbol="AAPL")
except RateLimitError:
    # Rate limited - automatic backoff applied
    pass
except CircuitBreakerOpenError:
    # Too many failures - circuit is open
    pass
except ReadOnlyError:
    # READ_ONLY mode and data not cached
    pass
except ProviderError as e:
    # General provider error
    print(f"Error: {e}")
```
