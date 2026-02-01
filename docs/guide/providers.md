# Providers

OmniData Nexus Core supports three data providers, each with specialized endpoints.

## FMP (Financial Modeling Prep)

13 endpoints for company fundamentals and financial data.

### Company Information

| Endpoint | Description | Parameters |
|----------|-------------|------------|
| `profile` | Company profile | `symbol` |
| `quote` | Real-time quote | `symbol` |

```python
profile = await loader.get_fmp_data(session, "profile", symbol="AAPL")
quote = await loader.get_fmp_data(session, "quote", symbol="AAPL")
```

### Financial Statements

| Endpoint | Description | Parameters |
|----------|-------------|------------|
| `income_statement` | Income statement | `symbol`, `period` |
| `balance_sheet` | Balance sheet | `symbol`, `period` |
| `cash_flow` | Cash flow statement | `symbol`, `period` |

```python
# Annual statements
income = await loader.get_fmp_data(
    session, "income_statement", symbol="AAPL", period="annual"
)

# Quarterly statements
balance = await loader.get_fmp_data(
    session, "balance_sheet", symbol="AAPL", period="quarterly"
)
```

### Metrics and Ratios

| Endpoint | Description | Parameters |
|----------|-------------|------------|
| `ratios` | Financial ratios | `symbol` |
| `growth` | Growth metrics | `symbol` |
| `key_metrics` | Key metrics | `symbol` |

```python
ratios = await loader.get_fmp_data(session, "ratios", symbol="AAPL")
growth = await loader.get_fmp_data(session, "growth", symbol="AAPL")
metrics = await loader.get_fmp_data(session, "key_metrics", symbol="AAPL")
```

### Historical Data

| Endpoint | Description | Parameters |
|----------|-------------|------------|
| `historical_price` | Historical OHLCV | `symbol`, `from`, `to` |
| `earnings_calendar` | Earnings dates | `from`, `to` |

```python
history = await loader.get_fmp_data(
    session, "historical_price",
    symbol="AAPL",
    **{"from": "2024-01-01", "to": "2024-12-31"}
)

earnings = await loader.get_fmp_data(
    session, "earnings_calendar",
    **{"from": "2025-01-01", "to": "2025-03-31"}
)
```

### Ownership

| Endpoint | Description | Parameters |
|----------|-------------|------------|
| `insider_trading` | Insider trades | `symbol` |
| `institutional_ownership` | Institutional holders | `symbol` |

```python
insider = await loader.get_fmp_data(session, "insider_trading", symbol="AAPL")
inst = await loader.get_fmp_data(session, "institutional_ownership", symbol="AAPL")
```

### Screening

| Endpoint | Description | Parameters |
|----------|-------------|------------|
| `screener` | Stock screener | Multiple filters |

```python
# Find large tech companies
results = await loader.get_fmp_data(
    session, "screener",
    marketCapMoreThan=100000000000,
    sector="Technology",
    isActivelyTrading=True
)
```

---

## Polygon.io

4 endpoints for market data and options.

| Endpoint | Description | Parameters |
|----------|-------------|------------|
| `aggs_daily` | Daily aggregates | `symbol`, `start`, `end` |
| `trades` | Tick-level trades | `symbol` |
| `options_snapshot` | Options chain | `underlying` |
| `market_snapshot` | Market overview | - |

```python
# Daily bars
aggs = await loader.get_polygon_data(
    session, "aggs_daily",
    symbol="SPY",
    start="2025-01-01",
    end="2025-01-31"
)

# Recent trades
trades = await loader.get_polygon_data(session, "trades", symbol="AAPL")

# Options chain
options = await loader.get_polygon_data(
    session, "options_snapshot", underlying="SPY"
)

# Market overview
snapshot = await loader.get_polygon_data(session, "market_snapshot")
```

---

## FRED (Federal Reserve Economic Data)

32+ macroeconomic series.

### Inflation

| Series ID | Description |
|-----------|-------------|
| `CPIAUCSL` | Consumer Price Index |
| `PCEPI` | PCE Price Index |
| `CPILFESL` | Core CPI |
| `T10YIE` | 10-Year Breakeven Inflation |

### Labor Market

| Series ID | Description |
|-----------|-------------|
| `UNRATE` | Unemployment Rate |
| `PAYEMS` | Nonfarm Payrolls |
| `ICSA` | Initial Claims |
| `AWHAETP` | Average Weekly Hours |

### Growth

| Series ID | Description |
|-----------|-------------|
| `GDP` | Gross Domestic Product |
| `GDPC1` | Real GDP |
| `INDPRO` | Industrial Production |
| `RSXFS` | Retail Sales |

### Interest Rates

| Series ID | Description |
|-----------|-------------|
| `FEDFUNDS` | Federal Funds Rate |
| `DGS10` | 10-Year Treasury |
| `DGS2` | 2-Year Treasury |
| `T10Y2Y` | 10Y-2Y Spread |

### Housing

| Series ID | Description |
|-----------|-------------|
| `HOUST` | Housing Starts |
| `CSUSHPINSA` | Case-Shiller Home Price |
| `MORTGAGE30US` | 30-Year Mortgage Rate |

### Usage

```python
# Fetch any FRED series
cpi = await loader.get_fred_data(session, "series", series_id="CPIAUCSL")
gdp = await loader.get_fred_data(session, "series", series_id="GDP")
rates = await loader.get_fred_data(session, "series", series_id="FEDFUNDS")

# Access observations
for obs in cpi.data['observations'][:5]:
    print(f"{obs['date']}: {obs['value']}")
```

---

## Provider Configuration

### Rate Limits

| Provider | Free Tier | Concurrency |
|----------|-----------|-------------|
| FMP | 250/day | 3 |
| Polygon | Limited | 10 |
| FRED | Unlimited | 1 |

### API Base URLs

| Provider | Base URL |
|----------|----------|
| FMP | `https://financialmodelingprep.com/stable/` |
| Polygon | `https://api.polygon.io/` |
| FRED | `https://api.stlouisfed.org/fred/` |
