# Providers API Reference

## Base Provider

::: data_loader.providers.base.BaseDataProvider
    options:
      show_root_heading: true
      show_source: true

## ProviderResponse

::: data_loader.providers.base.ProviderResponse
    options:
      show_root_heading: true

## FMP Provider

::: data_loader.providers.fmp.FMPProvider
    options:
      show_root_heading: true
      show_source: true

### Supported Endpoints

| Endpoint | Description | Required Params |
|----------|-------------|-----------------|
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
| `screener` | Stock screener | Various filters |

## Polygon Provider

::: data_loader.providers.polygon.PolygonProvider
    options:
      show_root_heading: true
      show_source: true

### Supported Endpoints

| Endpoint | Description | Required Params |
|----------|-------------|-----------------|
| `aggs_daily` | Daily aggregates | `symbol`, `start`, `end` |
| `trades` | Tick-level trades | `symbol` |
| `options_snapshot` | Options chain | `underlying` |
| `market_snapshot` | Market overview | - |

## FRED Provider

::: data_loader.providers.fred.FREDProvider
    options:
      show_root_heading: true
      show_source: true

### Supported Series

See the [Providers Guide](../guide/providers.md#fred-federal-reserve-economic-data) for the full list of supported FRED series.
