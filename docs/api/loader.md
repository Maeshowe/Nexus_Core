# DataLoader API Reference

::: data_loader.loader.DataLoader
    options:
      show_root_heading: true
      show_source: true

## DataLoaderStats

::: data_loader.loader.DataLoaderStats
    options:
      show_root_heading: true

## ReadOnlyError

::: data_loader.loader.ReadOnlyError
    options:
      show_root_heading: true

## OperatingMode

::: data_loader.config.OperatingMode
    options:
      show_root_heading: true

## Usage Examples

### Basic Usage

```python
import asyncio
import aiohttp
from data_loader import DataLoader

async def main():
    loader = DataLoader()

    async with aiohttp.ClientSession() as session:
        result = await loader.get_fmp_data(session, "profile", symbol="AAPL")
        print(result)

asyncio.run(main())
```

### Multiple Providers

```python
async def multi_provider():
    loader = DataLoader()

    async with aiohttp.ClientSession() as session:
        # FMP
        profile = await loader.get_fmp_data(session, "profile", symbol="AAPL")

        # Polygon
        aggs = await loader.get_polygon_data(
            session, "aggs_daily",
            symbol="SPY", start="2025-01-01", end="2025-01-31"
        )

        # FRED
        cpi = await loader.get_fred_data(session, "series", series_id="CPIAUCSL")

        return profile, aggs, cpi
```

### Operating Mode Control

```python
from data_loader import DataLoader, OperatingMode

loader = DataLoader()

# Switch to READ_ONLY
loader.set_operating_mode(OperatingMode.READ_ONLY)

# Check current mode
mode = loader.get_operating_mode()
print(f"Current mode: {mode}")
```

### Health Monitoring

```python
loader = DataLoader()

# ... make some requests ...

report = loader.get_api_health_report()
print(f"Overall status: {report['overall_status']}")

for provider, metrics in report['providers'].items():
    print(f"{provider}: {metrics['status']}")
```
