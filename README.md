# OmniData Nexus Core

> Modular, asynchronous DataLoader framework for financial and macroeconomic data aggregation.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

OmniData Nexus Core provides a unified interface for fetching and normalizing data from multiple financial APIs:

| Provider | Endpoints | Data Types |
|----------|-----------|------------|
| **FMP Ultimate** | 13 | Fundamentals, financials, ratios, insider trading |
| **Polygon.io** | 4 | Market data, trades, options snapshots |
| **FRED** | 32 series | Macroeconomic indicators |

### Key Features

- **Unified Interface** - Single `DataLoader` class for all providers
- **Async/Await** - Non-blocking I/O with `aiohttp`
- **Resilience Patterns** - Circuit breaker, exponential backoff, rate limiting
- **Intelligent Caching** - Filesystem JSON with atomic writes and TTL
- **QoS Management** - Provider-specific concurrency limits (FMP:3, Polygon:10, FRED:1)
- **Health Monitoring** - Real-time API status and error tracking

## Quick Start

### Installation

```bash
# Clone repository
git clone <repo_url> nexus_core
cd nexus_core

# Create virtual environment (Python 3.9+)
python3.9 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# For development
pip install -r requirements-dev.txt
```

### Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
# FMP_KEY=your_fmp_key
# POLYGON_KEY=your_polygon_key
# FRED_KEY=your_fred_key

# Secure the file
chmod 600 .env
```

### Basic Usage

```python
from src.data_loader import DataLoader
import aiohttp
import asyncio

async def main():
    loader = DataLoader()

    async with aiohttp.ClientSession() as session:
        # Fetch FMP company profile
        profile = await loader.get_fmp_data(session, "profile", symbol="AAPL")

        # Fetch Polygon daily aggregates
        aggs = await loader.get_polygon_data(
            session, "aggs_daily",
            symbol="SPY", start="2024-01-01", end="2024-01-31"
        )

        # Fetch FRED macroeconomic data
        cpi = await loader.get_fred_data(session, "CPIAUCSL")

        # Check API health
        health = loader.get_api_health_report()
        print(health)

asyncio.run(main())
```

## Project Structure

```
nexus_core/
├── src/
│   └── data_loader/
│       ├── __init__.py          # Package exports
│       ├── loader.py            # DataLoader unified interface
│       ├── config.py            # Configuration manager
│       ├── qos_router.py        # QoS Semaphore Router
│       ├── circuit_breaker.py   # Circuit Breaker Manager
│       ├── retry.py             # Retry & Backoff Handler
│       ├── http_client.py       # HTTP Client Layer
│       ├── cache.py             # Cache Manager
│       ├── health.py            # Health Monitor
│       └── providers/
│           ├── base.py          # BaseDataProvider
│           ├── fmp.py           # FMP Provider
│           ├── polygon.py       # Polygon Provider
│           └── fred.py          # FRED Provider
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── fixtures/
├── docs/                        # Documentation
├── data/                        # Cache directories (gitignored)
├── logs/                        # Log files (gitignored)
├── requirements.txt             # Production dependencies
├── requirements-dev.txt         # Development dependencies
└── .env.example                 # Environment template
```

## API Reference

### DataLoader

```python
class DataLoader:
    def __init__(self, mode: str = "LIVE"):
        """
        Initialize DataLoader.

        Args:
            mode: Operating mode - "LIVE" or "READ_ONLY"
        """

    async def get_fmp_data(self, session, endpoint: str, **params) -> dict:
        """Fetch data from FMP Ultimate API."""

    async def get_polygon_data(self, session, endpoint: str, **params) -> dict:
        """Fetch data from Polygon.io API."""

    async def get_fred_data(self, session, series_id: str, **params) -> dict:
        """Fetch data from FRED API."""

    def get_api_health_report(self) -> dict:
        """Get health status for all providers."""

    def set_operating_mode(self, mode: str) -> None:
        """Switch between LIVE and READ_ONLY modes."""
```

### Supported Endpoints

#### FMP (13 endpoints)
`screener`, `profile`, `quote`, `historical_price`, `earnings_calendar`, `balance_sheet`, `income_statement`, `cash_flow`, `ratios`, `growth`, `key_metrics`, `insider_trading`, `institutional_ownership`

#### Polygon (4 endpoints)
`aggs_daily`, `trades`, `options_snapshot`, `market_snapshot`

#### FRED (32 series)
Inflation, labor market, growth, housing, interest rates, and more. See [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md) for full list.

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m e2e
```

### Code Quality

```bash
# Linting
ruff check src/ tests/

# Type checking
mypy src/

# Format check
ruff format --check src/ tests/
```

## Documentation

- [REQUIREMENTS.md](docs/REQUIREMENTS.md) - Functional & non-functional requirements
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - System design & component diagrams
- [SECURITY.md](docs/SECURITY.md) - Security model & API key handling
- [TEST_STRATEGY.md](docs/TEST_STRATEGY.md) - Testing approach & coverage targets
- [DECISIONS.md](docs/DECISIONS.md) - Key technical decisions
- [ACTION_PLAN.md](docs/ACTION_PLAN.md) - Implementation roadmap

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

Based on MoneyFlows Data Loader v2.7.0 architecture.
