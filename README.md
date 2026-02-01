# OmniData Nexus Core

> Modular, asynchronous DataLoader framework for financial and macroeconomic data aggregation.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-441%20passed-brightgreen.svg)]()
[![Coverage](https://img.shields.io/badge/coverage-92%25-brightgreen.svg)]()

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
- **Operating Modes** - LIVE (API calls) and READ_ONLY (cache only)

## Installation

### From Source

```bash
# Clone repository
git clone https://github.com/Maeshowe/Nexus_Core.git
cd Nexus_Core

# Create virtual environment (Python 3.9+)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Or install dependencies directly
pip install -r requirements.txt

# For development (tests, linting)
pip install -r requirements-dev.txt
```

### Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env  # or your preferred editor
```

Required environment variables:

```bash
# API Keys (required for LIVE mode)
FMP_KEY=your_fmp_api_key
POLYGON_KEY=your_polygon_api_key
FRED_KEY=your_fred_api_key

# Optional settings
CACHE_TTL_DAYS=7          # Cache expiration (default: 7)
LOG_LEVEL=INFO            # DEBUG, INFO, WARNING, ERROR
OPERATING_MODE=LIVE       # LIVE or READ_ONLY
REQUEST_TIMEOUT=30        # API timeout in seconds
```

```bash
# Secure the file (Linux/macOS)
chmod 600 .env
```

## Quick Start

### Basic Usage

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

        # Fetch quote
        quote = await loader.get_fmp_data(session, "quote", symbol="AAPL")
        print(f"Price: ${quote.data['price']}")

asyncio.run(main())
```

### Multiple Providers

```python
async def fetch_analysis_data():
    loader = DataLoader()

    async with aiohttp.ClientSession() as session:
        # Company fundamentals (FMP)
        profile = await loader.get_fmp_data(session, "profile", symbol="AAPL")
        ratios = await loader.get_fmp_data(session, "ratios", symbol="AAPL")

        # Market data (Polygon)
        aggs = await loader.get_polygon_data(
            session, "aggs_daily",
            symbol="SPY",
            start="2025-01-01",
            end="2025-01-31"
        )

        # Macroeconomic context (FRED)
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

### Caching Behavior

```python
async def cached_example():
    loader = DataLoader()

    async with aiohttp.ClientSession() as session:
        # First call: fetches from API, caches result
        result1 = await loader.get_fmp_data(session, "profile", symbol="MSFT")
        print(f"From cache: {result1.from_cache}")  # False

        # Second call: returns cached data (no API call)
        result2 = await loader.get_fmp_data(session, "profile", symbol="MSFT")
        print(f"From cache: {result2.from_cache}")  # True

        # Force fresh data (bypass cache)
        result3 = await loader.get_fmp_data(
            session, "profile", symbol="MSFT", use_cache=False
        )
        print(f"From cache: {result3.from_cache}")  # False
```

### Health Monitoring

```python
async def check_health():
    loader = DataLoader()

    async with aiohttp.ClientSession() as session:
        # Make some requests
        await loader.get_fmp_data(session, "profile", symbol="AAPL")
        await loader.get_fred_data(session, "series", series_id="GDP")

    # Get health report
    report = loader.get_api_health_report()

    print(f"Operating Mode: {report['operating_mode']}")
    print(f"Overall Status: {report['overall_status']}")

    for provider, metrics in report['providers'].items():
        print(f"{provider}: {metrics['status']} "
              f"({metrics['successful_requests']}/{metrics['total_requests']} success)")
```

### READ_ONLY Mode

```python
from data_loader import DataLoader, OperatingMode

# Start in READ_ONLY mode (only serve cached data)
loader = DataLoader()
loader.set_operating_mode(OperatingMode.READ_ONLY)

async with aiohttp.ClientSession() as session:
    try:
        # This will work if data is cached
        result = await loader.get_fmp_data(session, "profile", symbol="AAPL")
    except ReadOnlyError as e:
        print(f"No cached data for {e.provider}:{e.endpoint}")
```

## Supported Endpoints

### FMP (13 endpoints)

| Endpoint | Description | Key Params |
|----------|-------------|------------|
| `profile` | Company profile | `symbol` |
| `quote` | Real-time quote | `symbol` |
| `historical_price` | Historical OHLCV | `symbol`, `from`, `to` |
| `earnings_calendar` | Earnings dates | `from`, `to` |
| `balance_sheet` | Balance sheet | `symbol`, `period` |
| `income_statement` | Income statement | `symbol`, `period` |
| `cash_flow` | Cash flow statement | `symbol`, `period` |
| `ratios` | Financial ratios | `symbol` |
| `growth` | Growth metrics | `symbol` |
| `key_metrics` | Key metrics | `symbol` |
| `insider_trading` | Insider trades | `symbol` |
| `institutional_ownership` | Institutional holders | `symbol` |
| `screener` | Stock screener | `marketCapMoreThan`, `sector`, etc. |

### Polygon (4 endpoints)

| Endpoint | Description | Key Params |
|----------|-------------|------------|
| `aggs_daily` | Daily aggregates | `symbol`, `start`, `end` |
| `trades` | Tick-level trades | `symbol` |
| `options_snapshot` | Options chain | `underlying` |
| `market_snapshot` | Market snapshot | - |

### FRED (32 series)

Inflation, labor market, growth, housing, interest rates, and more. See [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md) for full list.

## Project Structure

```
Nexus_Core/
├── src/data_loader/
│   ├── __init__.py          # Package exports
│   ├── loader.py            # DataLoader unified interface
│   ├── config.py            # Configuration manager
│   ├── qos_router.py        # QoS Semaphore Router
│   ├── circuit_breaker.py   # Circuit Breaker Manager
│   ├── retry.py             # Retry & Backoff Handler
│   ├── http_client.py       # HTTP Client Layer
│   ├── cache.py             # Cache Manager
│   ├── health.py            # Health Monitor
│   └── providers/
│       ├── base.py          # BaseDataProvider
│       ├── fmp.py           # FMP Provider
│       ├── polygon.py       # Polygon Provider
│       └── fred.py          # FRED Provider
├── tests/
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   └── e2e/                 # End-to-end tests
├── tools/diagnostics/       # Diagnostic tools
├── docs/                    # Documentation
├── scripts/                 # Utility scripts
└── data/                    # Cache (gitignored)
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest -m unit           # 300+ unit tests
pytest -m integration    # Integration tests
pytest -m e2e            # End-to-end scenarios

# Run specific test file
pytest tests/unit/test_loader.py -v
```

### Code Quality

```bash
# Linting
ruff check src/ tests/

# Type checking
mypy src/

# Format check
ruff format --check src/ tests/

# Fix formatting
ruff format src/ tests/
```

### Smoke Test

```bash
# Test with real API keys
python scripts/smoke_test.py
```

## Troubleshooting

### Common Issues

#### `ModuleNotFoundError: No module named 'data_loader'`

**Cause:** Package not installed or PYTHONPATH not set.

**Solution:**
```bash
# Option 1: Install in development mode
pip install -e .

# Option 2: Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

#### `FMP_KEY is required in LIVE mode`

**Cause:** Missing API keys in `.env` file.

**Solution:**
```bash
# Check if .env exists
cat .env

# Ensure keys are set
echo "FMP_KEY=your_key" >> .env
```

#### `Rate limit (429) errors`

**Cause:** Too many API requests.

**Solution:**
- The system automatically handles rate limits with exponential backoff
- FMP free tier: 250 calls/day
- Check your API plan limits
- Use caching to reduce API calls

#### `Circuit breaker OPEN`

**Cause:** Too many consecutive failures to a provider.

**Solution:**
```python
# Check circuit breaker status
report = loader.get_api_health_report()
print(report['circuit_breakers'])

# Wait for recovery timeout (default: 60s)
# Or restart the application
```

#### Cache not working

**Cause:** Cache directory permissions or TTL expired.

**Solution:**
```bash
# Check cache directory
ls -la data/

# Clear cache if needed
rm -rf data/fmp_cache data/polygon_cache data/fred_cache

# Check cache stats
python -c "
from data_loader import DataLoader
loader = DataLoader()
print(loader._cache.get_stats())
"
```

### Debug Mode

Enable debug logging for troubleshooting:

```bash
# In .env
LOG_LEVEL=DEBUG
```

Or programmatically:

```python
import logging
logging.getLogger('data_loader').setLevel(logging.DEBUG)
```

## Documentation

- [CHANGELOG.md](docs/CHANGELOG.md) - Version history
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
