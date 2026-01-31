# Architecture Design

> **Project:** OmniData Nexus Core
> **Version:** 1.0
> **Date:** 2026-01-31
> **Status:** Draft
> **Based on:** MoneyFlows Data Loader v2.7.0

---

## 1. Overview

### 1.1 Purpose

OmniData Nexus Core is a modular asynchronous Python framework providing a unified Data Access Layer for aggregating financial and macroeconomic data from heterogeneous API sources (FMP Ultimate, Polygon, FRED). It abstracts away provider-specific complexity, implements production-grade resilience patterns (circuit breaker, exponential backoff, QoS semaphore routing), and provides intelligent caching with atomic writes to enable fast, reliable quantitative research for a solo developer.

### 1.2 Architecture Goals

| Priority | Goal | Rationale |
|----------|------|-----------|
| 1 | Simplicity | Solo dev environment - prioritize maintainability over abstraction; avoid over-engineering |
| 2 | Resilience | Production-grade error handling (circuit breaker, backoff) to survive API failures without manual intervention |
| 3 | Performance | Maximize throughput via async I/O and provider-specific concurrency limits (QoS semaphore routing) |
| 4 | Extensibility | Plugin-style data sources allow easy addition of new APIs without core modifications |
| 5 | Transparency | Clear separation of concerns - caching, circuit breaking, rate limiting as orthogonal layers |

### 1.3 Architecture Style

**Selected:** Modular Monolith with Plugin Architecture

**Rationale:**
- **Single developer:** No operational overhead of distributed systems (no service mesh, no message brokers, no container orchestration)
- **Research workload:** Request patterns are batch-oriented, not requiring microservice-style independent scaling
- **Shared infrastructure:** Circuit breaker, caching, QoS router are common concerns - better centralized than duplicated
- **Deployment simplicity:** Single Python process, no network latency between components
- **Fast iteration:** Refactoring within a monolith is easier than coordinating across service boundaries

**Alternatives Considered:**

| Alternative | Pros | Cons | Why Rejected |
|-------------|------|------|--------------|
| Microservices (per provider) | Independent deployment, language flexibility | Operational complexity, network latency, distributed state management | Overkill for solo dev; no need for independent scaling |
| Serverless (AWS Lambda per endpoint) | Auto-scaling, pay-per-use | Cold start latency, vendor lock-in, difficult local testing | Research workload doesn't match serverless burst pattern |
| Pure Library (no framework) | Maximum flexibility | No standardization, repeated implementation of resilience patterns | Would duplicate circuit breaker/cache logic across consumers |

---

## 2. System Context

```
┌─────────────────────────────────────────────────────────────────────┐
│                        EXTERNAL SYSTEMS                              │
│                                                                      │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐      │
│  │  FMP Ultimate│      │  Polygon.io  │      │  FRED API    │      │
│  │              │      │              │      │              │      │
│  │ 13 endpoints │      │ 4 endpoints  │      │ 32 series    │      │
│  │ Rate: Plan   │      │ Rate: 5-10/m │      │ Rate: ~120/m │      │
│  └──────┬───────┘      └──────┬───────┘      └──────┬───────┘      │
│         │                     │                     │              │
│         └─────────────────────┼─────────────────────┘              │
│                               │                                    │
│                     HTTPS/REST over Internet                        │
│                               │                                    │
│                               ▼                                    │
│              ┌────────────────────────────────┐                     │
│              │   OmniData Nexus Core          │                     │
│              │   (Python 3.9+ Framework)      │                     │
│              │                                │                     │
│              │  Unified DataLoader Interface  │                     │
│              │  + Circuit Breaker             │                     │
│              │  + QoS Semaphore Router        │                     │
│              │  + Intelligent Cache           │                     │
│              └────────────────┬───────────────┘                     │
│                               │                                    │
│                               ▼                                    │
│                ┌───────────────────────────┐                        │
│                │  Quantitative Researcher  │                        │
│                │  (Primary User)           │                        │
│                │  - Jupyter Notebooks      │                        │
│                │  - Python Scripts         │                        │
│                └───────────────────────────┘                        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### External Interfaces

| System | Protocol | Direction | Purpose | Rate Limit |
|--------|----------|-----------|---------|------------|
| FMP Ultimate | HTTPS REST (JSON) | OUT | Company fundamentals, insider trading, financials | Plan-dependent (3 concurrent via QoS) |
| Polygon.io | HTTPS REST (JSON) | OUT | Market data, trades, options snapshots | 5 req/min (free), 10 concurrent via QoS |
| FRED | HTTPS REST (JSON) | OUT | Macroeconomic indicators (32 series) | ~120 req/min recommended, 1 concurrent via QoS |

---

## 3. Component Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                       OmniData Nexus Core                             │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────────────────────────────────────────────┐         │
│  │              DataLoader (Unified Interface)              │         │
│  │  - get_fmp_data(session, endpoint, **params)            │         │
│  │  - get_polygon_data(session, endpoint, **params)        │         │
│  │  - get_fred_data(session, series_id, **params)          │         │
│  │  - get_api_health_report() → dict                       │         │
│  │  - set_operating_mode(mode: LIVE | READ_ONLY)           │         │
│  └────────────┬──────────────────────────────┬──────────────┘         │
│               │                              │                        │
│               ▼                              ▼                        │
│  ┌─────────────────────┐        ┌─────────────────────────┐          │
│  │  QoS Semaphore      │        │   Circuit Breaker       │          │
│  │  Router             │        │   Manager               │          │
│  │                     │        │                         │          │
│  │  - FMP: max=3       │        │  - threshold: 20%       │          │
│  │  - Polygon: max=10  │        │  - states: CLOSED/      │          │
│  │  - FRED: max=1      │        │    OPEN/HALF-OPEN       │          │
│  │  - acquire(provider)│        │  - per-provider state   │          │
│  └─────────┬───────────┘        └──────────┬──────────────┘          │
│            │                               │                         │
│            └───────────┬───────────────────┘                         │
│                        ▼                                             │
│       ┌────────────────────────────────────────┐                     │
│       │      Provider Abstraction Layer        │                     │
│       │  (Base class: BaseDataProvider)        │                     │
│       └────────────────┬───────────────────────┘                     │
│                        │                                             │
│        ┌───────────────┼───────────────┐                             │
│        ▼               ▼               ▼                             │
│  ┌──────────┐   ┌──────────┐   ┌──────────────┐                     │
│  │   FMP    │   │ Polygon  │   │    FRED      │                     │
│  │ Provider │   │ Provider │   │  Provider    │                     │
│  │          │   │          │   │              │                     │
│  │ - 13 EPs │   │ - 4 EPs  │   │ - 32 series  │                     │
│  │ - auth() │   │ - auth() │   │ - auth()     │                     │
│  │ - fetch()│   │ - fetch()│   │ - fetch()    │                     │
│  │ - norm() │   │ - norm() │   │ - norm()     │                     │
│  └────┬─────┘   └────┬─────┘   └─────┬────────┘                     │
│       │              │               │                              │
│       └──────────────┼───────────────┘                              │
│                      ▼                                              │
│         ┌────────────────────────────┐                              │
│         │  Retry & Backoff Handler   │                              │
│         │  - Exponential delay       │                              │
│         │  - Jitter randomization    │                              │
│         │  - Max retries: 3          │                              │
│         │  - Retry only 5xx/timeout  │                              │
│         └────────────┬───────────────┘                              │
│                      ▼                                              │
│         ┌────────────────────────────┐                              │
│         │     HTTP Client Layer      │                              │
│         │  (aiohttp.ClientSession)   │                              │
│         │  - Connection pooling      │                              │
│         │  - Timeout management      │                              │
│         │  - API key sanitization    │                              │
│         └────────────┬───────────────┘                              │
│                      │                                              │
│         ┌────────────┴───────────────┐                              │
│         ▼                            ▼                              │
│  ┌──────────────┐            ┌──────────────────┐                   │
│  │ Cache Manager│            │ Health Monitor   │                   │
│  │              │            │                  │                   │
│  │ - get_cached()│            │ - request_count  │                   │
│  │ - set_cache()│            │ - error_count    │                   │
│  │ - TTL: 7d    │            │ - error_rate     │                   │
│  │ - atomic     │            │ - rate_limit_%   │                   │
│  │   writes     │            │ - circuit_state  │                   │
│  └──────┬───────┘            └──────────────────┘                   │
│         │                                                           │
│         ▼                                                           │
│  ┌──────────────────────────────────────┐                           │
│  │      Filesystem (JSON Cache)         │                           │
│  │  data/                               │                           │
│  │  ├── fmp_cache/{endpoint}/{date}/    │                           │
│  │  │   └── {symbol}.json               │                           │
│  │  ├── polygon_cache/{endpoint}/       │                           │
│  │  │   └── {hash}.json                 │                           │
│  │  └── fred_cache/{series_id}/         │                           │
│  │      └── {date_range}.json           │                           │
│  └──────────────────────────────────────┘                           │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

### Component Descriptions

| Component | Responsibility | Dependencies | Location |
|-----------|----------------|--------------|----------|
| **DataLoader** | Unified entry point for all data sources; orchestrates QoS, circuit breaker, provider selection | All components | `src/data_loader/loader.py` |
| **QoS Semaphore Router** | Enforces provider-specific concurrency limits; prevents rate limit violations | Config Manager | `src/data_loader/qos_router.py` |
| **Circuit Breaker Manager** | Monitors error rates; halts requests when threshold exceeded (>20%); manages recovery | Health Monitor | `src/data_loader/circuit_breaker.py` |
| **BaseDataProvider** | Abstract base class defining provider interface (auth, fetch, normalize, cache_key) | None | `src/data_loader/providers/base.py` |
| **FMP Provider** | FMP-specific implementation; 13 endpoints (screener, profile, financials, etc.) | BaseDataProvider, HTTP Client | `src/data_loader/providers/fmp.py` |
| **Polygon Provider** | Polygon-specific implementation; 4 endpoints (aggs, trades, options, snapshot) | BaseDataProvider, HTTP Client | `src/data_loader/providers/polygon.py` |
| **FRED Provider** | FRED-specific implementation; 32 economic series | BaseDataProvider, HTTP Client | `src/data_loader/providers/fred.py` |
| **Retry & Backoff Handler** | Implements exponential backoff with jitter; retries transient failures (5xx, timeouts) | HTTP Client | `src/data_loader/retry.py` |
| **HTTP Client Layer** | Async HTTP requests via aiohttp; connection pooling; timeout management | aiohttp.ClientSession | `src/data_loader/http_client.py` |
| **Cache Manager** | Read/write JSON cache; provider-specific paths; TTL management; atomic writes (temp+rename) | Filesystem | `src/data_loader/cache.py` |
| **Health Monitor** | Tracks request counts, error rates, rate limit consumption; generates health reports | None | `src/data_loader/health.py` |
| **Config Manager** | Loads API keys from environment; manages settings (TTLs, concurrency limits, timeouts) | python-dotenv | `src/data_loader/config.py` |

---

## 4. Data Architecture

### 4.1 Data Model

**Domain Entities:**

```
┌─────────────────────────┐
│   DataRequest           │
├─────────────────────────┤
│ provider: str           │  (fmp | polygon | fred)
│ endpoint: str           │  (profile, aggs_daily, CPIAUCSL)
│ params: dict            │  (symbol, start_date, etc.)
│ cache_key: str          │  MD5(provider+endpoint+params)
└─────────────────────────┘
           │
           │ 1:1
           ▼
┌─────────────────────────┐
│   DataResponse          │
├─────────────────────────┤
│ data: dict | list       │  Normalized response
│ source: str             │  (cache | api)
│ timestamp: datetime     │  Fetch time
│ provider: str           │
│ error: str | None       │  Error message if failed
└─────────────────────────┘
           │
           │ 1:N
           ▼
┌─────────────────────────┐
│   CacheEntry            │
├─────────────────────────┤
│ cache_key: str          │  Unique identifier
│ data: dict              │  Response payload
│ created_at: datetime    │  Cache creation time
│ ttl_seconds: int        │  Time to live (default 604800)
│ provider: str           │
│ endpoint: str           │
└─────────────────────────┘
```

**Health Monitoring Model:**

```
┌─────────────────────────┐       ┌─────────────────────────┐
│   HealthReport          │       │   ProviderHealth        │
├─────────────────────────┤       ├─────────────────────────┤
│ timestamp: datetime     │───1:N─│ provider: str           │
│ overall_status: str     │       │ total_requests: int     │
│ providers: list[...]    │       │ errors: int             │
└─────────────────────────┘       │ error_rate: float       │
                                  │ circuit_state: str      │
                                  │ rate_limit_pct: float   │
                                  │ last_error: str | None  │
                                  └─────────────────────────┘
```

### 4.2 Storage Decisions

| Data Type | Storage | Format | Rationale |
|-----------|---------|--------|-----------|
| API Responses | Filesystem (JSON) | `data/{provider}_cache/{path}/{file}.json` | Simple, versioned, human-readable; no DB overhead |
| Configuration | Environment variables + `.env` file | Key-value pairs | Standard practice; keeps secrets out of code |
| API Keys | Environment variables | `FMP_KEY`, `POLYGON_KEY`, `FRED_KEY` | Security best practice; never in version control |
| Logs | Filesystem (rotating) | `logs/nexus_core.log` | Standard Python logging; rotation prevents disk fill |
| Metrics (future) | In-memory counters | Python dicts | Lightweight; no persistence needed for research workload |

**Cache Path Strategy:**

| Provider | Path Pattern | Example | Rationale |
|----------|--------------|---------|-----------|
| FMP | `data/fmp_cache/{endpoint}/{date}/{symbol}.json` | `data/fmp_cache/profile/2026-01-31/AAPL.json` | Date-based expiration; easy manual inspection |
| Polygon | `data/polygon_cache/{endpoint}/{hash}.json` | `data/polygon_cache/aggs_daily/a3f2e9d1b8c4.json` | Hash handles complex query params (date ranges) |
| FRED | `data/fred_cache/{series_id}/{date_range}.json` | `data/fred_cache/CPIAUCSL/2020-01-01_2026-01-31.json` | Series-centric; date range in filename |

### 4.3 Data Flow

**Happy Path (Cache Miss):**

```
User Request
     │
     ▼
[DataLoader.get_fmp_data("profile", symbol="AAPL")]
     │
     ├─────▶ [Check Operating Mode] ──READONLY──▶ [Cache.get()] ──MISS──▶ [Raise Error]
     │                                   │
     │                                  LIVE
     ▼                                   │
[Cache.get(key)] ──HIT──▶ [Return cached data]
     │                                   │
    MISS                                 │
     │                                   │
     ▼                                   │
[Circuit Breaker.check()] ──OPEN──▶ [Raise CircuitOpenError]
     │                                   │
   CLOSED                                │
     │                                   │
     ▼                                   │
[QoS Semaphore.acquire(fmp)] ──max=3────┤
     │                                   │
     ▼                                   │
[FMPProvider.fetch(endpoint, params)]   │
     │                                   │
     ├──▶ [HTTP GET] ──429──▶ [Parse Retry-After] ──▶ [Sleep] ──▶ [Retry]
     │                 │
     │                5xx
     │                 │
     ├──▶ [Retry Handler] ──▶ [Exponential Backoff + Jitter] ──▶ [Retry up to 3x]
     │                 │
     │                200
     ▼                 │
[Validate Schema]      │
     │                 │
     ▼                 │
[Normalize Data]       │
     │                 │
     ▼                 │
[Cache.set(key, data, ttl=7d)] ──atomic write──▶ [temp.json] ──rename──▶ [final.json]
     │                 │
     ▼                 │
[QoS Semaphore.release(fmp)]
     │
     ▼
[Return DataResponse]
```

**Error Path (Circuit Breaker Opens):**

```
Multiple Failures (>20% error rate)
     │
     ▼
[Circuit Breaker] ──error_rate > 0.2──▶ [State = OPEN]
     │
     ▼
[Subsequent Requests] ──▶ [Immediate Failure: CircuitOpenError]
     │
     ▼
[After timeout period] ──▶ [State = HALF-OPEN]
     │
     ▼
[Single test request] ──SUCCESS──▶ [State = CLOSED] ──▶ [Normal operation]
                       │
                     FAILURE
                       │
                       ▼
                  [State = OPEN]
```

---

## 5. Technology Stack

| Layer | Technology | Version | Rationale |
|-------|------------|---------|-----------|
| **Language** | Python | 3.9+ | Async/await improvements; widespread in quant research; asyncio stability |
| **Async HTTP** | aiohttp | ≥3.8 | Production-ready async HTTP client; connection pooling; timeout control |
| **Environment** | python-dotenv | ≥0.19 | Standard .env file loading; keeps secrets out of code |
| **Testing** | pytest | ≥7.0 | Industry standard; excellent async support via pytest-asyncio |
| **Coverage** | pytest-cov | ≥3.0 | Coverage reporting; integrated with pytest |
| **Type Hints** | typing (built-in) | - | Improved IDE support; runtime type validation possible |
| **Logging** | logging (built-in) | - | Standard library; rotating file handlers; no external deps |
| **JSON** | json (built-in) | - | Sufficient for cache; no serialization edge cases |
| **Hashing** | hashlib (built-in) | - | MD5 for cache keys (speed prioritized over crypto security) |

### Dependencies

| Package | Purpose | License | Risk Assessment |
|---------|---------|---------|-----------------|
| aiohttp | Async HTTP client | Apache 2.0 | Low - mature, widely used |
| python-dotenv | Environment variable loading | BSD-3 | Low - simple, no network calls |
| pytest | Testing framework | MIT | Low - dev dependency only |
| pytest-cov | Coverage reporting | MIT | Low - dev dependency only |
| pytest-asyncio | Async test support | Apache 2.0 | Low - dev dependency only |

**No database dependencies** - Filesystem cache sufficient for research workload.

---

## 6. Architecture Decisions

| ID | Decision | Context | Consequences |
|----|----------|---------|--------------|
| **AD-001** | Use Modular Monolith over Microservices | Solo developer; research workload (batch-oriented, not user-facing); shared infrastructure (circuit breaker, cache, QoS) | (+) Simple deployment, fast iteration, no network overhead<br>(-) All components share failure domain |
| **AD-002** | Filesystem JSON cache (not Redis/DB) | Single user; dataset fits in memory; human-readable cache aids debugging | (+) Zero external dependencies, simple backups, inspectable<br>(-) No TTL auto-expiration, manual cleanup needed |
| **AD-003** | Provider-specific concurrency limits (QoS Semaphore) | Each API has different rate limits (FMP:3, Polygon:10, FRED:1) | (+) Prevents rate limit violations, maximizes throughput<br>(-) Requires tuning per API subscription tier |
| **AD-004** | Circuit Breaker per provider (not global) | API failures are independent (FMP down ≠ Polygon down) | (+) Isolates failures, allows partial service<br>(-) More complex state management |
| **AD-005** | Atomic cache writes (temp + rename) | Concurrent reads during writes could read partial JSON | (+) Guarantees consistency, prevents corruption<br>(-) Extra filesystem operation per write |
| **AD-006** | Plugin architecture (BaseDataProvider) | Need to add new APIs (Alpha Vantage, IEX) without core changes | (+) Extensibility, separation of concerns<br>(-) Slight abstraction overhead |
| **AD-007** | Exponential backoff with jitter (not linear) | Prevent thundering herd on API recovery | (+) Better distribution of retries, faster recovery<br>(-) More complex retry logic |
| **AD-008** | Operating modes (LIVE vs READ-ONLY) | Support offline analysis; prevent accidental API calls during testing | (+) Explicit control, enables airplane mode<br>(-) Mode management adds complexity |
| **AD-009** | Schema validation (warn, don't fail) | API schemas evolve; prefer partial data over total failure | (+) Robustness to API changes, research continuity<br>(-) May mask breaking changes |
| **AD-010** | Async/await (not threading) | I/O-bound workload; Python GIL limits thread scaling | (+) Efficient concurrency, single-threaded simplicity<br>(-) All code must be async-compatible |

---

## 7. Deployment

### 7.1 Deployment Model

```
┌─────────────────────────────────────────────────────────────┐
│                  Local Development Environment               │
│                      (macOS / Linux)                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Python 3.9+ Virtual Environment                       │ │
│  │  (venv / conda)                                        │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │                                                         │ │
│  │  ┌──────────────────────────────────────────────────┐  │ │
│  │  │  OmniData Nexus Core (src/)                      │  │ │
│  │  │  - DataLoader                                    │  │ │
│  │  │  - Providers (FMP, Polygon, FRED)                │  │ │
│  │  │  - Circuit Breaker, QoS Router, Cache            │  │ │
│  │  └──────────────────────────────────────────────────┘  │ │
│  │                                                         │ │
│  │  ┌──────────────────────────────────────────────────┐  │ │
│  │  │  Consumer Applications                           │  │ │
│  │  │  - Jupyter Notebooks (analysis/)                 │  │ │
│  │  │  - Python Scripts (scripts/)                     │  │ │
│  │  └──────────────────────────────────────────────────┘  │ │
│  │                                                         │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Filesystem Storage                                    │ │
│  │  - data/fmp_cache/                                     │ │
│  │  - data/polygon_cache/                                 │ │
│  │  - data/fred_cache/                                    │ │
│  │  - logs/nexus_core.log                                 │ │
│  │  - .env (API keys)                                     │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                         │
                         │ HTTPS
                         ▼
         ┌───────────────────────────────┐
         │  External APIs (Internet)     │
         │  - FMP Ultimate               │
         │  - Polygon.io                 │
         │  - FRED                       │
         └───────────────────────────────┘
```

### 7.2 Environments

| Environment | Purpose | Configuration | API Keys |
|-------------|---------|---------------|----------|
| **Development** | Local testing, research analysis | `.env` file with real API keys | Real (rate-limited tier) |
| **Testing** | Unit/integration tests | `.env.test` with mock API keys | Mock/test keys |
| **CI (future)** | Automated testing | Environment variables, mock HTTP responses | No real API calls |

**No Production Environment** - Research tool runs locally only.

### 7.3 Installation

```bash
# 1. Clone repository
git clone <repo_url> nexus_core
cd nexus_core

# 2. Create virtual environment
python3.9 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure API keys
cp .env.example .env
# Edit .env with real API keys:
# FMP_KEY=your_fmp_key
# POLYGON_KEY=your_polygon_key
# FRED_KEY=your_fred_key

# 5. Create cache directories
mkdir -p data/fmp_cache data/polygon_cache data/fred_cache logs

# 6. Verify installation
python -c "from src.data_loader import DataLoader; print('OK')"
```

**Target:** <5 minutes to first successful fetch.

---

## 8. Cross-Cutting Concerns

| Concern | Approach | Implementation |
|---------|----------|----------------|
| **Error Handling** | Layered strategy: retry transient (5xx), circuit break persistent (>20%), fail fast permanent (4xx) | Try/except in each layer; custom exceptions (CircuitOpenError, CacheMissError, ValidationError) |
| **Logging** | Structured logging with provider/endpoint context; API key sanitization | Python `logging` module; rotating file handler (10MB, 5 backups); log level configurable via env |
| **Configuration** | Environment variables for secrets; Python module for defaults | `config.py` loads from `.env`; fallback defaults for non-secrets (TTL=7d, max_retries=3) |
| **Monitoring** | In-memory counters for requests/errors; health report API | `HealthMonitor` class tracks per-provider metrics; exposed via `get_api_health_report()` |
| **Security** | API key sanitization in logs; no keys in cache files or errors | Regex-based key redaction in log formatter; validate no keys in JSON before cache write |
| **Concurrency** | Async/await for I/O; semaphores for rate limiting | `asyncio.Semaphore` per provider; single event loop per process |
| **Testing** | Unit tests (mocked HTTP), integration tests (real HTTP), coverage >80% | pytest with pytest-asyncio; `aioresponses` for HTTP mocking; separate test fixtures per provider |
| **Documentation** | Inline docstrings (Google style); architecture docs; API reference | Sphinx-ready docstrings; `docs/` folder for ADRs and guides |

---

## 9. Quality Attributes

| Attribute | Target | How Achieved | Measurement |
|-----------|--------|--------------|-------------|
| **Performance** | Single API request <2s p95 | Async I/O, connection pooling, cache hits | Timer wrapper on fetch methods |
| **Scalability** | 50+ concurrent requests (within QoS limits) | asyncio.gather(), semaphore-controlled concurrency | Benchmark script with varying concurrency |
| **Reliability** | >95% success rate (excluding API outages) | Circuit breaker, exponential backoff, retry logic | success_count / total_count metric |
| **Maintainability** | >80% test coverage; clear separation of concerns | Modular design, plugin architecture, comprehensive tests | pytest-cov report |
| **Extensibility** | Add new provider in <4 hours | BaseDataProvider abstract class with template | Time-to-implement new source metric |
| **Usability** | <5 minute setup; single-method API calls | Minimal dependencies, clear examples, unified interface | Timed installation by new user |
| **Security** | No API keys in logs/cache/git | Sanitization filters, .gitignore, env var validation | Automated grep in CI |
| **Availability** | Partial service during single API outage | Per-provider circuit breaker, independent failure domains | Health check during simulated outage |

---

## 10. Risks & Mitigations

| Risk | Probability | Impact | Mitigation | Owner |
|------|-------------|--------|------------|-------|
| **API schema breaking change** | Medium | High | Schema validation with warnings; graceful degradation; version pinning in provider | Developer |
| **Rate limit exhaustion** | Medium | Medium | QoS semaphore enforces limits; 429 handling; warning at 80% consumption | Framework (automated) |
| **API service outage** | Medium | Medium | Circuit breaker halts requests; cache serves stale data; clear error messages | Framework (automated) |
| **Cache corruption** | Low | Medium | Atomic writes (temp+rename); validate JSON before write; backup strategy | Framework (automated) |
| **Dependency vulnerability** | Low | Medium | Minimal dependencies; regular `pip audit`; version pinning in requirements.txt | Developer |
| **Thundering herd on recovery** | Low | Low | Exponential backoff with jitter; circuit breaker half-open state (single test request) | Framework (automated) |
| **Memory exhaustion (large datasets)** | Low | High | Not mitigated in v1.0; future: streaming/pagination; document memory limits | Developer (docs) |
| **API key leakage** | Low | Critical | .gitignore for .env; sanitization in logs; no keys in cache; pre-commit hook validation | Developer + Framework |

---

## 11. Future Considerations

**Not in v1.0, but architectural support planned:**

| Feature | Architectural Preparation | Effort Estimate |
|---------|--------------------------|-----------------|
| **Plugin Discovery** | BaseDataProvider already abstract; add registry pattern | 8h |
| **Metrics Export (Prometheus)** | HealthMonitor counters ready; add exposition endpoint | 12h |
| **Request Batching** | Provider interface supports batch methods; add batch scheduler | 16h |
| **Streaming/Pagination** | Add async iterator support to provider interface | 20h |
| **Database Cache Backend** | Cache abstraction layer ready; implement SQLite/Postgres backend | 24h |
| **Dark Pool Detection** | Polygon trades endpoint fetched; add filter logic | 8h |

---

## 12. Constraints & Assumptions

### Constraints

- **Python 3.9+** required (async/await, type hints)
- **Single user** - no multi-tenancy, no authentication
- **Local execution** - no distributed deployment
- **Internet required** - no offline mode beyond cache (READ-ONLY mode)
- **Concurrency limits** - FMP (3), Polygon (10), FRED (1) enforced

### Assumptions

| ID | Assumption | Validation | Risk if Wrong |
|----|------------|------------|---------------|
| A-001 | Datasets fit in memory (<10GB per request) | Monitor memory usage during testing | Need streaming/pagination (20h effort) |
| A-002 | API schemas stable for 6+ months | Version detection in provider | Manual normalization updates needed |
| A-003 | Solo developer has valid API keys for all 3 providers | Check at startup | Graceful degradation to available providers |
| A-004 | Filesystem cache sufficient (no concurrency from multiple processes) | Document limitation | Need file locking or DB backend |
| A-005 | Research workload tolerates 7-day stale data | User configurable TTL | Reduce TTL or invalidate cache manually |

---

## Approval

| Role | Name | Date | Status |
|------|------|------|--------|
| Author | Architect Agent | 2026-01-31 | ✅ Generated |
| Reference | MoneyFlows Data Loader v2.7.0 | - | ✅ Integrated |
| Owner | Solo Developer | | ☐ Pending Review |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-31 | Architect Agent | Initial architecture design based on approved requirements |

---

*Architecture designed for simplicity, resilience, and extensibility. Built on proven patterns from MoneyFlows Data Loader v2.7.0.*
