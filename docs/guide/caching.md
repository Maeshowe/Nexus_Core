# Caching

OmniData Nexus Core includes an intelligent caching system to reduce API calls and improve performance.

## Overview

- **Storage**: Filesystem-based JSON cache
- **TTL**: Configurable time-to-live (default: 7 days)
- **Atomic Writes**: Safe concurrent access
- **Per-Provider**: Separate cache directories

## Cache Structure

```
data/
├── fmp_cache/
│   ├── profile_AAPL.json
│   ├── quote_MSFT.json
│   └── ...
├── polygon_cache/
│   ├── aggs_daily_SPY_2025-01-01_2025-01-31.json
│   └── ...
└── fred_cache/
    ├── series_CPIAUCSL.json
    └── ...
```

## Automatic Caching

All API responses are automatically cached:

```python
# First call: API request, result cached
result1 = await loader.get_fmp_data(session, "profile", symbol="AAPL")
print(result1.from_cache)  # False

# Second call: served from cache
result2 = await loader.get_fmp_data(session, "profile", symbol="AAPL")
print(result2.from_cache)  # True
```

## Cache Control

### Bypass Cache

```python
# Force fresh data from API
result = await loader.get_fmp_data(
    session, "profile", symbol="AAPL", use_cache=False
)
```

### Cache Stats

```python
stats = loader._cache.get_stats()

print(f"Total entries: {stats['total_entries']}")
print(f"Total size: {stats['total_size_mb']:.2f} MB")
print(f"Oldest entry: {stats['oldest_entry']}")
print(f"Newest entry: {stats['newest_entry']}")
```

### Clear Cache

```bash
# Clear all cache
rm -rf data/fmp_cache data/polygon_cache data/fred_cache

# Clear specific provider
rm -rf data/fmp_cache
```

## TTL Configuration

### Environment Variable

```bash
# In .env
CACHE_TTL_DAYS=14  # 2 weeks
```

### Programmatic

```python
loader = DataLoader()
loader._cache.ttl_days = 14
```

## Cache Entry Format

Each cached file contains:

```json
{
  "data": { ... },
  "timestamp": "2025-01-31T10:30:00Z",
  "provider": "fmp",
  "endpoint": "profile",
  "params": {
    "symbol": "AAPL"
  },
  "ttl_days": 7
}
```

## Cache Key Generation

Cache keys are generated from:

1. Provider name
2. Endpoint name
3. Sorted parameters

```python
# These generate the same cache key:
await loader.get_fmp_data(session, "profile", symbol="AAPL")
await loader.get_fmp_data(session, "profile", symbol="AAPL")

# This generates a different key:
await loader.get_fmp_data(session, "profile", symbol="MSFT")
```

## READ_ONLY Mode

In READ_ONLY mode, only cached data is served:

```python
from data_loader import DataLoader, OperatingMode

loader = DataLoader()
loader.set_operating_mode(OperatingMode.READ_ONLY)

# Works if cached
result = await loader.get_fmp_data(session, "profile", symbol="AAPL")

# Raises ReadOnlyError if not cached
try:
    result = await loader.get_fmp_data(session, "profile", symbol="UNKNOWN")
except ReadOnlyError:
    print("Data not in cache")
```

## Best Practices

### 1. Pre-warm Cache

For batch analysis, pre-warm the cache:

```python
async def prewarm_cache(symbols: list[str]):
    loader = DataLoader()
    async with aiohttp.ClientSession() as session:
        for symbol in symbols:
            await loader.get_fmp_data(session, "profile", symbol=symbol)
            await loader.get_fmp_data(session, "ratios", symbol=symbol)
    print(f"Cached data for {len(symbols)} symbols")
```

### 2. Use Appropriate TTL

- **Real-time data** (quotes): Short TTL or `use_cache=False`
- **Fundamentals** (profiles): Default TTL (7 days)
- **Historical data**: Long TTL (30+ days)

### 3. Monitor Cache Size

```python
stats = loader._cache.get_stats()
if stats['total_size_mb'] > 1000:  # 1 GB
    print("Consider clearing old cache entries")
```

## Troubleshooting

### Cache not working

```bash
# Check directory exists and is writable
ls -la data/

# Check permissions
chmod 755 data/
```

### Stale data

```python
# Force refresh
result = await loader.get_fmp_data(
    session, "profile", symbol="AAPL", use_cache=False
)
```

### Cache corruption

```bash
# Remove corrupted entry
rm data/fmp_cache/profile_AAPL.json

# Or clear all
rm -rf data/
```
