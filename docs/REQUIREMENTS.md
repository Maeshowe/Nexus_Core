# Requirements Specification

> **Project:** OmniData Nexus Core
> **Version:** 1.0
> **Date:** 2026-01-31
> **Status:** Draft
> **Based on:** MoneyFlows Data Loader v2.7.0

---

## 1. Executive Summary

OmniData Nexus Core is a modular, asynchronous Python framework serving as a centralized Data Access Layer for aggregating financial and macroeconomic data from multiple API sources. Built upon the proven MoneyFlows Data Loader architecture, it provides a unified interface for **50 endpoints** across FMP Ultimate (13), Polygon (4), and FRED (33) APIs. The framework features intelligent caching, circuit breaker patterns, rate limit management via QoS Semaphore Router, and comprehensive health monitoring.

---

## 2. Problem Statement

### 2.1 Current Situation
Quantitative finance research requires data from multiple specialized APIs:
- **FMP Ultimate**: Fundamental data (financials, ratios, metrics, insider trading)
- **Polygon.io**: Market data (daily aggregates, trades, options snapshots)
- **FRED**: Macroeconomic indicators (32 key series across inflation, employment, growth)

Each API has different authentication, response formats, rate limits, and availability patterns.

### 2.2 Problem
There is no unified framework that:
- Provides a single interface for heterogeneous financial data sources
- Implements production-grade resilience (circuit breaker, exponential backoff)
- Manages concurrent requests with provider-specific limits
- Caches responses intelligently with atomic writes
- Monitors API health and rate limit consumption automatically

### 2.3 Impact
Without this framework:
- Slow data acquisition (sequential fetching)
- Brittle code prone to API-specific failures
- Rate limit violations leading to throttling/bans
- Inconsistent error handling across sources
- Time spent on infrastructure instead of analysis

---

## 3. Stakeholders

| Stakeholder | Role | Primary Need |
|-------------|------|--------------|
| Quantitative Researcher | Primary User | Fast, reliable access to normalized financial data |
| API Providers (FMP, Polygon, FRED) | External Services | Compliance with rate limits and ToS |
| Future Contributors | Developers | Clear extension points for new data sources |

---

## 4. Functional Requirements

### 4.1 Core (MVP) - MUST

| ID | Feature | Description | Acceptance Criteria |
|----|---------|-------------|---------------------|
| FR-001 | Unified DataLoader Interface | Central `DataLoader` class with `get_fmp_data()`, `get_polygon_data()`, `get_fred_data()` methods | - Consistent method signatures<br>- Returns normalized data structures<br>- Supports all 50 endpoints |
| FR-002 | FMP Ultimate Integration (13 endpoints) | Async client for all FMP endpoints | - screener, profile, quote, historical_price<br>- earnings_calendar, balance_sheet, income_statement<br>- ratios, growth, key_metrics, cash_flow<br>- insider_trading, institutional_ownership |
| FR-003 | Polygon Integration (4 endpoints) | Async client for Polygon API | - aggs_daily: `/v2/aggs/ticker/{symbol}/range/1/day/{start}/{end}`<br>- trades: `/v3/trades/{symbol}`<br>- options_snapshot: `/v3/snapshot/options/{symbol}`<br>- market_snapshot: `/v2/snapshot/locale/us/markets/stocks/tickers` |
| FR-004 | FRED Integration (32 series) | Async client for FRED API | - Inflation: CPIAUCSL, CPILFESL, PCEPI, PCEPILFE<br>- Labor: UNRATE, PAYEMS, CES0500000003, ECIWAG, CIVPART<br>- Growth: GDPC1, GPDI, PNFI + equipment/R&D<br>- Housing: HOUST, PERMIT, HSN1F, CSUSHPINSA<br>- Rates: DGS10, FEDFUNDS, MORTGAGE30US<br>- LEI: AWHMAN, DGORDER, ICSA, IC4WSA<br>- Sentiment: UMCSENT, UMCSENTEXP |
| FR-005 | QoS Semaphore Router | Provider-specific concurrency limits | - FMP: max 3 concurrent requests<br>- Polygon: max 10 concurrent requests<br>- FRED: max 1 concurrent request<br>- Configurable via `api.concurrency.*` |
| FR-006 | Intelligent Caching | Multi-strategy cache with atomic writes | - FMP: `data/fmp_cache/{endpoint}/{date}/{symbol}.json`<br>- Polygon: `data/polygon_cache/{endpoint}/{hash}.json`<br>- TTL: 7 days default<br>- Atomic writes (temp file + rename) |
| FR-007 | Circuit Breaker | Automatic request halting on high error rate | - Opens when error rate > 20%<br>- Half-open state for recovery testing<br>- Closed state for normal operation<br>- Per-provider circuit state |
| FR-008 | Exponential Backoff with Jitter | Retry strategy for transient failures | - Configurable max retries (default: 3)<br>- Exponential delay (1s, 2s, 4s...)<br>- Random jitter to prevent thundering herd<br>- Only retry 5xx and timeouts |
| FR-009 | Rate Limit Handling | HTTP 429 response management | - Provider-specific cooldown times<br>- Parse Retry-After headers<br>- Warning at 80% consumption<br>- Automatic request throttling |
| FR-010 | Health Check System | API availability monitoring | - `get_api_health_report()` method<br>- Returns: total_requests, errors, error_rate, circuit_breaker state<br>- Per-provider status (UP/DOWN/DEGRADED) |
| FR-011 | Schema-based Validation | Response structure verification | - Validate against expected schemas<br>- Return `None` + warning on invalid<br>- Log validation failures |
| FR-012 | Operating Modes | LIVE vs READ-ONLY operation | - LIVE: API as primary, write-through cache<br>- READ-ONLY: Cache only, 0 API calls guaranteed |
| FR-013 | Configuration Management | External config for credentials and settings | - Environment variables: `FMP_KEY`, `POLYGON_KEY`, `FRED_KEY`<br>- `.env` file support<br>- `core.config_manager` integration |
| FR-014 | API Key Sanitization | Security in logging | - Automatic removal of API keys from logs<br>- No keys in error messages<br>- No keys in cache files |

### 4.2 Important - SHOULD

| ID | Feature | Description | Acceptance Criteria |
|----|---------|-------------|---------------------|
| FR-101 | Cache TTL Configuration | Per-endpoint cache expiration | - Configurable TTL per data type<br>- Override defaults via config<br>- Automatic cache invalidation |
| FR-102 | Request Batching | Combine similar requests | - Batch within time window<br>- Respect API batch limits<br>- Transparent to caller |
| FR-103 | Metrics Export | Operational telemetry | - Request count per source<br>- Response times (p50, p95, p99)<br>- Cache hit/miss rates |
| FR-104 | Graceful Degradation | Partial success handling | - Return available data on partial failure<br>- Log failed sources<br>- Clear error attribution |

### 4.3 Nice to Have - COULD

| ID | Feature | Description |
|----|---------|-------------|
| FR-201 | Plugin Architecture | Dynamic loading of new data source implementations |
| FR-202 | Dark Pool Detection | Block trade identification (min_block_size: 10000, min_notional configurable) |
| FR-203 | Data Export | Export to Parquet/HDF5 formats |
| FR-204 | CLI Tool | Command-line interface for manual queries |
| FR-205 | Async Iterator Support | Stream large datasets without full memory load |

### 4.4 Out of Scope - WON'T (this version)

| Feature | Reason |
|---------|--------|
| GUI Dashboard | Focus on programmatic API |
| Database Persistence | Caller responsible for storage |
| Data Analysis/Modeling | Framework provides data, not analytics |
| Multi-user Authentication | Single-user research tool |
| WebSocket Streaming | REST endpoints sufficient for research |

---

## 5. Non-Functional Requirements

| ID | Category | Requirement | Target | Measurement |
|----|----------|-------------|--------|-------------|
| NFR-001 | Performance | Single API request latency | <2s p95 | Timed fetch operations |
| NFR-002 | Performance | Parallel fetch speedup | >3x for 10 concurrent vs sequential | Benchmark comparison |
| NFR-003 | Reliability | Successful request rate | >95% (excluding API outages) | Success/total ratio |
| NFR-004 | Reliability | Retry recovery rate | >80% of retryable failures | Retry success tracking |
| NFR-005 | Reliability | Circuit breaker threshold | Opens at >20% error rate | Error rate monitoring |
| NFR-006 | Maintainability | Code test coverage | >80% line coverage | pytest-cov report |
| NFR-007 | Security | API key protection | No keys in code, logs, git, cache | Audit + grep verification |
| NFR-008 | Scalability | Concurrent requests | 50+ simultaneous (within QoS limits) | Load testing |
| NFR-009 | Usability | Setup time | <5 minutes to first fetch | Timed installation |
| NFR-010 | Compatibility | Python version | 3.9+ | CI matrix testing |
| NFR-011 | Data Integrity | Cache atomicity | No partial/corrupt cache files | Concurrent write tests |

---

## 6. User Stories

### US-001: Fetch Company Fundamentals

```
AS A quantitative researcher
I WANT to fetch financial fundamentals for a stock symbol
SO THAT I can analyze company financial health

ACCEPTANCE CRITERIA:
- [ ] Can call loader.get_fmp_data(session, "profile", symbol="AAPL")
- [ ] Can fetch balance_sheet, income_statement, cash_flow, ratios
- [ ] Data normalized with consistent field names
- [ ] Circuit breaker protects against API failures
- [ ] Response cached for 7 days by default
```

### US-002: Fetch Multi-Source Data in Parallel

```
AS A quantitative researcher
I WANT to fetch FMP + Polygon + FRED data concurrently
SO THAT I can correlate fundamental, market, and macro data efficiently

ACCEPTANCE CRITERIA:
- [ ] All requests execute in parallel (respecting QoS limits)
- [ ] Total time ≈ slowest single request
- [ ] Partial success handled (return what succeeds, log failures)
- [ ] Results unified in consistent structure
```

### US-003: Monitor API Health

```
AS A quantitative researcher
I WANT to check API health before running batch jobs
SO THAT I can avoid wasted time on failing APIs

ACCEPTANCE CRITERIA:
- [ ] Can call loader.get_api_health_report()
- [ ] Returns per-provider: total_requests, errors, error_rate, circuit_breaker state
- [ ] Circuit breaker state visible: CLOSED/OPEN/HALF-OPEN
- [ ] Rate limit consumption visible
```

### US-004: Work Offline with Cache

```
AS A quantitative researcher
I WANT to run analysis using only cached data
SO THAT I can work without API calls (airplane mode, rate limit exhausted)

ACCEPTANCE CRITERIA:
- [ ] Can set operating mode to READ-ONLY
- [ ] Guarantees 0 API calls in READ-ONLY mode
- [ ] Returns cached data if available
- [ ] Clear error if cache miss in READ-ONLY mode
```

### US-005: Handle Rate Limits Gracefully

```
AS A quantitative researcher
I WANT the system to manage rate limits automatically
SO THAT I don't get blocked by API providers

ACCEPTANCE CRITERIA:
- [ ] QoS Semaphore limits concurrent requests (FMP:3, Polygon:10, FRED:1)
- [ ] HTTP 429 triggers provider-specific cooldown
- [ ] Warning logged at 80% rate limit consumption
- [ ] Request automatically delayed if limit would be exceeded
```

### US-006: Fetch FRED Macroeconomic Series

```
AS A quantitative researcher
I WANT to fetch key macroeconomic indicators
SO THAT I can incorporate macro factors in my models

ACCEPTANCE CRITERIA:
- [ ] Can fetch all 32 FRED series (see Appendix A)
- [ ] Inflation: CPIAUCSL, CPILFESL, PCEPI, PCEPILFE
- [ ] Labor: UNRATE, PAYEMS, CIVPART
- [ ] Rates: DGS10, FEDFUNDS, MORTGAGE30US
- [ ] Housing: HOUST, CSUSHPINSA
- [ ] Data normalized to consistent time series format
```

### US-007: Extend with New Data Source

```
AS A quantitative researcher
I WANT to add a new API (e.g., Alpha Vantage) easily
SO THAT I can expand data coverage as needed

ACCEPTANCE CRITERIA:
- [ ] Clear base class/interface to implement
- [ ] New source inherits circuit breaker, caching, QoS
- [ ] Documentation shows extension example
- [ ] No core code modification required
```

---

## 7. Constraints

### 7.1 Technical
- Python 3.9+ required (asyncio improvements)
- aiohttp for async HTTP
- Concurrency limits: FMP (3), Polygon (10), FRED (1)
- No API keys in version control or logs
- Atomic cache writes (temp + rename pattern)

### 7.2 Business
- API access limited by subscription tier (FMP Ultimate required)
- Solo developer project
- Research use only

### 7.3 API-Specific
- FMP: Rate limits vary by plan
- Polygon: 5 req/min (free tier), higher on paid
- FRED: No official limit, recommend 120 req/min max

---

## 8. Assumptions

| ID | Assumption | Impact if Wrong |
|----|------------|-----------------|
| A-001 | Internet connectivity reliable | Need offline queue mode |
| A-002 | API schemas remain stable | Manual normalization updates needed |
| A-003 | User has valid API keys for all 3 sources | Source unavailable; handle gracefully |
| A-004 | Data fits in memory | Need streaming/pagination |
| A-005 | POSIX environment (macOS/Linux) | Windows path adjustments needed |

---

## 9. Dependencies

| ID | Dependency | Type | Version | Risk |
|----|------------|------|---------|------|
| D-001 | aiohttp | PyPI | ≥3.8 | Low |
| D-002 | asyncio | Built-in | - | Low |
| D-003 | core.config_manager | Internal | - | Low |
| D-004 | python-dotenv | PyPI | ≥0.19 | Low |
| D-005 | FMP API | External Service | - | Medium |
| D-006 | Polygon API | External Service | - | Medium |
| D-007 | FRED API | External Service | - | Low |
| D-008 | pytest / pytest-cov | PyPI (dev) | - | Low |

---

## 10. Glossary

| Term | Definition |
|------|------------|
| DataLoader | Central class providing unified access to all data sources |
| Circuit Breaker | Pattern that stops requests when error rate exceeds threshold (20%) |
| QoS Semaphore Router | Concurrency limiter enforcing per-provider request limits |
| Exponential Backoff | Retry strategy with increasing delays (1s, 2s, 4s...) + jitter |
| TTL | Time To Live - cache validity duration (default 7 days) |
| Atomic Write | File write pattern using temp file + rename to prevent corruption |
| LIVE Mode | Operating mode where API is primary source with write-through cache |
| READ-ONLY Mode | Operating mode serving only from cache (0 API calls) |
| FMP | Financial Modeling Prep - fundamental data provider |
| Polygon | Market data provider for equities, options, indices |
| FRED | Federal Reserve Economic Data - macroeconomic indicators |

---

## Appendix A: Complete Endpoint Reference

### A.1 FMP Endpoints (13)

| Endpoint | URL Pattern | Description |
|----------|-------------|-------------|
| screener | `/stable/company-screener` | Stock screener |
| profile | `/stable/profile` | Company profile |
| quote | `/stable/quote` | Current price |
| historical_price | `/stable/historical-price-eod/full` | Historical EOD prices |
| earnings_calendar | `/stable/earnings-calendar` | Earnings dates |
| balance_sheet | `/stable/balance-sheet-statement` | Balance sheet |
| income_statement | `/stable/income-statement` | Income statement |
| cash_flow | `/stable/cash-flow-statement` | Cash flow statement |
| ratios | `/stable/ratios` | Financial ratios |
| growth | `/stable/financial-growth` | Growth metrics |
| key_metrics | `/stable/key-metrics` | Key metrics |
| insider_trading | `/stable/insider-trading/search` | Insider transactions |
| institutional_ownership | `/stable/institutional-ownership/latest` | Institutional holdings |

### A.2 Polygon Endpoints (4)

| Endpoint | URL Pattern | Description |
|----------|-------------|-------------|
| aggs_daily | `/v2/aggs/ticker/{symbol}/range/1/day/{start}/{end}` | Daily OHLCV |
| trades | `/v3/trades/{symbol}` | Individual trades |
| options_snapshot | `/v3/snapshot/options/{symbol}` | Options snapshot |
| market_snapshot | `/v2/snapshot/locale/us/markets/stocks/tickers` | Full market snapshot |

### A.3 FRED Series (32)

| Category | Series IDs | Frequency |
|----------|------------|-----------|
| Inflation | CPIAUCSL, CPILFESL, PCEPI, PCEPILFE | Monthly |
| Labor Market | UNRATE, PAYEMS, CES0500000003, ECIWAG, CIVPART | Monthly/Quarterly |
| Growth | GDPC1, GPDI, PNFI, Y033RC1Q027SBEA, Y006RC1Q027SBEA | Quarterly |
| Trade | EXPGS, IMPGS, NETEXP | Quarterly |
| Housing | HOUST, PERMIT, HSN1F, EXHOSLUSM495S, CSUSHPINSA | Monthly |
| Interest Rates | DGS10, FEDFUNDS, MORTGAGE30US | Daily/Monthly/Weekly |
| Leading Indicators | AWHMAN, DGORDER, ICSA, IC4WSA | Monthly/Weekly |
| Sentiment | UMCSENT, UMCSENTEXP | Monthly |
| Policy | USEPUINDXD | Monthly |

**Total: 50 endpoints** (13 FMP + 4 Polygon + 1 FRED base + 32 FRED series)

---

## Approval

| Role | Name | Date | Status |
|------|------|------|--------|
| Author | Analyst Agent | 2026-01-31 | ✅ Generated |
| Reference | MoneyFlows Data Loader v2.7.0 | - | ✅ Integrated |
| Owner | Solo Developer | | ☐ Pending |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1 | 2026-01-31 | Analyst Agent | Initial draft |
| 0.2 | 2026-01-31 | Analyst Agent | Integrated MoneyFlows Data Loader v2.7.0 specs |

---

*Based on MoneyFlows Data Loader v2.7.0 Technical Documentation*
