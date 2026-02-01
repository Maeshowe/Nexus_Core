# OmniData Nexus Core

> Modular, asynchronous DataLoader framework for financial and macroeconomic data aggregation.

## Overview

OmniData Nexus Core provides a unified interface for fetching and normalizing data from multiple financial APIs:

| Provider | Endpoints | Data Types |
|----------|-----------|------------|
| **FMP Ultimate** | 13 | Fundamentals, financials, ratios, insider trading |
| **Polygon.io** | 4 | Market data, trades, options snapshots |
| **FRED** | 32 series | Macroeconomic indicators |

## Key Features

- **Unified Interface** - Single `DataLoader` class for all providers
- **Async/Await** - Non-blocking I/O with `aiohttp`
- **Resilience Patterns** - Circuit breaker, exponential backoff, rate limiting
- **Intelligent Caching** - Filesystem JSON with atomic writes and TTL
- **QoS Management** - Provider-specific concurrency limits
- **Health Monitoring** - Real-time API status and error tracking
- **Operating Modes** - LIVE (API calls) and READ_ONLY (cache only)

## Quick Example

```python
import asyncio
import aiohttp
from data_loader import DataLoader

async def main():
    loader = DataLoader()

    async with aiohttp.ClientSession() as session:
        # Fetch company profile from FMP
        profile = await loader.get_fmp_data(session, "profile", symbol="AAPL")
        print(f"Company: {profile.data['companyName']}")

        # Fetch macroeconomic data from FRED
        cpi = await loader.get_fred_data(session, "series", series_id="CPIAUCSL")
        print(f"CPI observations: {len(cpi.data)}")

asyncio.run(main())
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      DataLoader                              │
│                   (Unified Interface)                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ FMP Provider│  │Polygon Prov.│  │ FRED Prov.  │          │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘          │
├─────────┴────────────────┴────────────────┴─────────────────┤
│                    Resilience Layer                          │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐         │
│  │Circuit Breaker│ │ Retry/Backoff│ │ QoS Router  │         │
│  └──────────────┘ └──────────────┘ └──────────────┘         │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐         │
│  │  HTTP Client │ │ Cache Manager│ │Health Monitor│         │
│  └──────────────┘ └──────────────┘ └──────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

## Getting Started

<div class="grid cards" markdown>

-   :material-download:{ .lg .middle } __Installation__

    ---

    Install OmniData Nexus Core from source

    [:octicons-arrow-right-24: Installation](getting-started/installation.md)

-   :material-cog:{ .lg .middle } __Configuration__

    ---

    Configure API keys and settings

    [:octicons-arrow-right-24: Configuration](getting-started/configuration.md)

-   :material-rocket-launch:{ .lg .middle } __Quick Start__

    ---

    Start fetching data in minutes

    [:octicons-arrow-right-24: Quick Start](getting-started/quickstart.md)

</div>

## License

MIT License - see [LICENSE](https://github.com/Maeshowe/Nexus_Core/blob/main/LICENSE) for details.
