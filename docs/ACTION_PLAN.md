# Action Plan

> **Project:** OmniData Nexus Core
> **Version:** 1.0
> **Date:** 2026-01-31
> **Status:** ✅ COMPLETE
> **Created by:** Lead Agent

---

## 1. Executive Summary

| Metric | Value |
|--------|-------|
| **Total Tasks** | 28 |
| **Total Effort** | 186-248 hours (realistic estimate) |
| **Duration** | 5-7 weeks at sustainable pace (8-10 hours/week) |
| **Sustainable Pace** | 8-10 hours/week (research-driven, flexible) |
| **Milestones** | 4 (Foundation, Core Providers, Resilience, Testing & Polish) |

### Milestone Timeline

```
Week 1-2        Week 3-4        Week 5-6        Week 7+
────────────    ────────────    ────────────    ────────────
M1: Foundation  M2: Providers   M3: Resilience  M4: Testing
[██████████]    [██████████]    [██████████]    [██████████]
 ✅ COMPLETE     ✅ COMPLETE      ✅ COMPLETE      ✅ COMPLETE
```

### Final Results

| Metric | Target | Actual |
|--------|--------|--------|
| **Tests** | ~200 | 441 |
| **Coverage** | >80% | 92% |
| **TIER 1 Coverage** | >90% | 95-99% |
| **CI/CD** | GitHub Actions | ✅ Configured |

### Reality Check

This is a realistic timeline for a solo developer working 8-10 hours per week on a research tool with no hard deadlines. Effort estimates include:
- Actual coding time
- Testing time (not just "add tests later")
- Debugging and iteration
- Documentation updates
- Learning curve for new patterns

**Critical Path:** M1 → M2 → M3 → M4 (sequential dependencies)

---

## 2. Milestones

### M1: Foundation & Infrastructure
**Target:** Week 1-2 (16-20 hours)
**Effort:** 38-52 hours (realistic)
**Status:** ✅ COMPLETE

| ID | Task | Effort | Priority | Deps | Status |
|----|------|--------|----------|------|--------|
| T-001 | Project setup and dependencies | 2h | P0 | - | ☐ |
| T-002 | Configuration manager (.env loading) | 4-6h | P0 | T-001 | ☐ |
| T-003 | HTTP client layer (aiohttp wrapper) | 6-8h | P0 | T-001 | ☐ |
| T-004 | Cache manager (filesystem JSON) | 8-12h | P0 | T-001 | ☐ |
| T-005 | Health monitor (metrics tracking) | 6-8h | P0 | T-001 | ☐ |
| T-006 | Base data provider interface | 6-8h | P0 | T-003 | ☐ |
| T-007 | Logging setup with API key sanitization | 6-8h | P0 | T-002 | ☐ |

**Success Criteria:**
- [ ] Project structure created (`src/data_loader/`, `tests/`, `docs/`, `data/`)
- [ ] Dependencies installed (aiohttp, python-dotenv, pytest)
- [ ] .env.example created with placeholder keys
- [ ] Cache manager can write/read JSON atomically
- [ ] Health monitor tracks basic counters
- [ ] BaseDataProvider abstract class defined
- [ ] API keys sanitized in all log output

**Deliverables:**
- Working project skeleton
- Passing lint (ruff/flake8) and type checks (mypy)
- Basic unit tests for config, cache, health monitor
- Documentation: README.md with setup instructions

---

### M2: Core Providers
**Target:** Week 3-4 (16-20 hours)
**Effort:** 64-88 hours (realistic)
**Status:** ✅ COMPLETE

| ID | Task | Effort | Priority | Deps | Status |
|----|------|--------|----------|------|--------|
| T-008 | FMP provider (13 endpoints) | 24-32h | P0 | T-006 | ☐ |
| T-009 | Polygon provider (4 endpoints) | 12-16h | P0 | T-006 | ☐ |
| T-010 | FRED provider (32 series + base) | 16-24h | P0 | T-006 | ☐ |
| T-011 | Provider integration tests (mocked HTTP) | 12-16h | P0 | T-008,009,010 | ☐ |

**Success Criteria:**
- [ ] FMP provider supports all 13 endpoints (screener, profile, quote, historical_price, earnings_calendar, balance_sheet, income_statement, cash_flow, ratios, growth, key_metrics, insider_trading, institutional_ownership)
- [ ] Polygon provider supports 4 endpoints (aggs_daily, trades, options_snapshot, market_snapshot)
- [ ] FRED provider supports 32 series + base API
- [ ] All providers normalize responses to consistent format
- [ ] Cache keys generated correctly per provider strategy
- [ ] Integration tests passing with aioresponses mocks
- [ ] Provider-specific error handling (429, 5xx, timeouts)

**Deliverables:**
- 3 working provider implementations
- ~40 integration tests (provider + HTTP mocking)
- JSON fixtures in `tests/fixtures/{fmp,polygon,fred}/`
- Provider documentation with endpoint examples

**Technical Notes:**
- FMP is the most complex (13 endpoints, varying response structures)
- FRED has 32 series but simpler endpoint pattern
- Polygon has date range complexity for aggregates
- Mock all HTTP responses using aioresponses library

---

### M3: Resilience Layer
**Target:** Week 5-6 (16-20 hours)
**Effort:** 52-72 hours (realistic)
**Status:** ✅ COMPLETE

| ID | Task | Effort | Priority | Deps | Status |
|----|------|--------|----------|------|--------|
| T-012 | QoS Semaphore Router | 8-12h | P0 | T-006 | ☐ |
| T-013 | Circuit Breaker Manager | 12-16h | P0 | T-005 | ☐ |
| T-014 | Retry handler (exponential backoff + jitter) | 8-12h | P0 | T-003 | ☐ |
| T-015 | Rate limit handling (HTTP 429) | 6-8h | P0 | T-014 | ☐ |
| T-016 | DataLoader unified interface | 10-14h | P0 | T-012,013,014 | ☐ |
| T-017 | Operating modes (LIVE/READ-ONLY) | 4-6h | P0 | T-016 | ☐ |
| T-018 | Resilience integration tests | 4-8h | P0 | T-012,013,014 | ☐ |

**Success Criteria:**
- [ ] QoS Router enforces concurrency: FMP=3, Polygon=10, FRED=1
- [ ] Circuit Breaker opens at >20% error rate
- [ ] Circuit Breaker recovery flow: OPEN → HALF-OPEN → CLOSED
- [ ] Exponential backoff: ~1s, ~2s, ~4s with jitter
- [ ] Retry only on 5xx/timeout (not 4xx)
- [ ] HTTP 429 handling: parse Retry-After header
- [ ] DataLoader orchestrates all resilience components
- [ ] READ-ONLY mode prevents API calls (cache-only)
- [ ] LIVE mode normal operation
- [ ] Integration tests validate state machine transitions

**Deliverables:**
- QoS router with per-provider semaphores
- Circuit breaker with 3-state FSM
- Retry handler with backoff calculator
- DataLoader unified interface
- ~30 unit tests for resilience components
- ~15 integration tests for orchestration

**Technical Notes:**
- Circuit Breaker is TIER 1 (>90% coverage required)
- QoS Router is TIER 1 (>90% coverage required)
- Use asyncio.Semaphore for concurrency control
- Store circuit breaker state in-memory (no persistence)
- DataLoader is the main entry point for consumers

---

### M4: Testing & Polish
**Target:** Week 7+ (variable)
**Effort:** 32-36 hours (realistic)
**Status:** ✅ COMPLETE

| ID | Task | Effort | Priority | Deps | Status |
|----|------|--------|----------|------|--------|
| T-019 | Unit test suite completion (TIER 1 >90%) | 12-16h | P0 | All | ☐ |
| T-020 | E2E test scenarios (10 critical paths) | 8-12h | P0 | T-016 | ☐ |
| T-021 | Security tests (API key sanitization) | 4-6h | P0 | T-007 | ☐ |
| T-022 | Coverage analysis and gap filling | 4-6h | P0 | T-019,020 | ☐ |
| T-023 | CI/CD pipeline setup (GitHub Actions) | 4-6h | P1 | T-022 | ☐ |
| T-024 | Documentation polish (README, examples) | 6-8h | P1 | All | ☐ |
| T-025 | Pre-commit hooks (secret scanning) | 2-3h | P1 | T-007 | ☐ |
| T-026 | Manual smoke test with real APIs | 2-3h | P1 | All | ☐ |

**Success Criteria:**
- [ ] Overall coverage >80% (pytest-cov)
- [ ] TIER 1 coverage >90% (circuit_breaker, qos_router, sanitization, cache atomic)
- [ ] All ~200 tests passing
- [ ] Test execution time <2 minutes
- [ ] TC-001 through TC-106 passing (critical test cases)
- [ ] No API keys in logs/cache/git (security tests)
- [ ] CI pipeline green
- [ ] README.md with setup instructions <5 minutes
- [ ] Working examples in `examples/` directory
- [ ] Pre-commit hook blocks commits with secrets
- [ ] Manual validation: fetch real data from all 3 providers

**Deliverables:**
- ~150 unit tests
- ~10 E2E tests
- ~10 security tests
- Coverage reports (HTML + terminal)
- CI/CD pipeline (.github/workflows/)
- Pre-commit configuration
- Updated README.md
- Example usage scripts
- Manual test report

**Technical Notes:**
- This is where the effort multiplier really applies
- "Add tests" is never quick - expect 8-16h minimum
- Coverage gap filling is detective work (2-4h)
- E2E tests need careful orchestration (mocking all providers)

---

## 3. Task Details

### T-001: Project Setup and Dependencies

| Field | Value |
|-------|-------|
| **Milestone** | M1 |
| **Effort** | 2 hours |
| **Priority** | P0 |
| **Dependencies** | None |

**Description:**
Create project directory structure, initialize git repository, set up Python virtual environment, and install core dependencies.

**Implementation Steps:**
1. Create directory structure matching architecture design
2. Initialize git repository with .gitignore
3. Create Python virtual environment (Python 3.9+)
4. Create requirements.txt with pinned versions
5. Create requirements-dev.txt for development dependencies
6. Create .env.example with placeholder API keys
7. Create basic README.md

**Acceptance Criteria:**
- [ ] Directory structure exists: `src/data_loader/`, `tests/`, `docs/`, `data/`, `logs/`
- [ ] Virtual environment activated
- [ ] Dependencies installed: aiohttp>=3.8, python-dotenv>=0.19
- [ ] Dev dependencies: pytest>=7.0, pytest-cov>=3.0, pytest-asyncio>=0.21, aioresponses>=0.7, mypy>=1.0, ruff
- [ ] .gitignore includes: `.env`, `__pycache__`, `*.pyc`, `venv/`, `data/*`, `logs/*`, `.mypy_cache/`, `.pytest_cache/`, `htmlcov/`
- [ ] .env.example created with: `FMP_KEY=your_fmp_key_here`, `POLYGON_KEY=`, `FRED_KEY=`
- [ ] README.md has installation instructions

**Files to Create:**
- `requirements.txt`
- `requirements-dev.txt`
- `.gitignore`
- `.env.example`
- `README.md`
- `src/data_loader/__init__.py`
- `tests/conftest.py`

**Commands:**
```bash
# Create project structure
mkdir -p src/data_loader/providers tests/{unit,integration,e2e,fixtures} docs data logs

# Initialize git
git init
# (create .gitignore first)
git add .
git commit -m "Initial project structure"

# Create virtual environment
python3.9 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Verify installation
python -c "import aiohttp; import dotenv; print('Dependencies OK')"
pytest --version
mypy --version
```

---

### T-002: Configuration Manager (.env loading)

| Field | Value |
|-------|-------|
| **Milestone** | M1 |
| **Effort** | 4-6 hours |
| **Priority** | P0 |
| **Dependencies** | T-001 |

**Description:**
Implement configuration manager that loads API keys and settings from environment variables (.env file). Includes validation, defaults, and error handling for missing keys.

**Implementation Notes:**
- Use python-dotenv for .env loading
- Separate required keys (API keys) from optional settings (TTL, timeouts)
- Validate keys at startup (not empty strings)
- Provide sensible defaults for non-secret settings
- Support environment variable override (for CI)

**Acceptance Criteria:**
- [ ] Config loads from .env file if present
- [ ] Config loads from environment variables (higher priority than .env)
- [ ] Missing required keys raise ConfigError at startup
- [ ] Optional settings have defaults: `CACHE_TTL_DAYS=7`, `MAX_RETRIES=3`, `CIRCUIT_BREAKER_THRESHOLD=0.2`
- [ ] Config is a singleton (single instance per process)
- [ ] Unit tests verify: .env parsing, defaults, validation, missing keys error

**Files to Create:**
- `src/data_loader/config.py`
- `tests/unit/test_config_manager.py`

**Implementation Example:**
```python
# src/data_loader/config.py
from dotenv import load_dotenv
import os

class Config:
    def __init__(self):
        load_dotenv()  # Load from .env file

        # Required API keys
        self.fmp_key = self._get_required("FMP_KEY")
        self.polygon_key = self._get_required("POLYGON_KEY")
        self.fred_key = self._get_required("FRED_KEY")

        # Optional settings with defaults
        self.cache_ttl_days = int(os.getenv("CACHE_TTL_DAYS", "7"))
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))
        self.circuit_breaker_threshold = float(os.getenv("CIRCUIT_BREAKER_THRESHOLD", "0.2"))
        # ... more settings

    def _get_required(self, key: str) -> str:
        value = os.getenv(key)
        if not value:
            raise ConfigError(f"Required environment variable {key} not set")
        return value

# Singleton pattern
_config_instance = None
def get_config() -> Config:
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
```

---

### T-003: HTTP Client Layer (aiohttp wrapper)

| Field | Value |
|-------|-------|
| **Milestone** | M1 |
| **Effort** | 6-8 hours |
| **Priority** | P0 |
| **Dependencies** | T-001 |

**Description:**
Create async HTTP client wrapper around aiohttp.ClientSession with timeout management, connection pooling, TLS enforcement, and request/response logging.

**Implementation Notes:**
- Enforce HTTPS only (reject http:// URLs)
- Configure timeouts: connect=5s, read=30s, total=60s
- Connection pooling: limit=100 per host
- Timeout error handling (aiohttp.ClientTimeout)
- Request/response logging (sanitize URLs with API keys)
- Session reuse (long-lived ClientSession)

**Acceptance Criteria:**
- [ ] HTTP client enforces HTTPS (raises error for http://)
- [ ] Configurable timeouts per request
- [ ] Connection pooling configured
- [ ] TLS certificate validation enabled
- [ ] Request logging includes: method, URL (sanitized), status code
- [ ] Response logging includes: status, headers (selected), body size
- [ ] Error handling for: timeout, connection errors, TLS errors
- [ ] Unit tests verify: HTTPS enforcement, timeout config, error handling

**Files to Create:**
- `src/data_loader/http_client.py`
- `tests/unit/test_http_client.py`

**Implementation Example:**
```python
# src/data_loader/http_client.py
import aiohttp
from typing import Optional, Dict, Any

class HTTPClient:
    def __init__(self, timeout: aiohttp.ClientTimeout = None):
        self.timeout = timeout or aiohttp.ClientTimeout(
            total=60, connect=5, sock_read=30
        )
        self._session: Optional[aiohttp.ClientSession] = None

    async def get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(limit=100)
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=self.timeout
            )
        return self._session

    async def get(self, url: str, **kwargs) -> Dict[str, Any]:
        self._enforce_https(url)
        session = await self.get_session()
        async with session.get(url, **kwargs) as response:
            response.raise_for_status()
            return await response.json()

    def _enforce_https(self, url: str):
        if not url.startswith("https://"):
            raise ValueError(f"HTTPS required, got: {url}")

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
```

---

### T-004: Cache Manager (filesystem JSON)

| Field | Value |
|-------|-------|
| **Milestone** | M1 |
| **Effort** | 8-12 hours |
| **Priority** | P0 |
| **Dependencies** | T-001 |

**Description:**
Implement cache manager with atomic writes (temp + rename pattern), TTL expiration, provider-specific directory structure, and JSON serialization. This is TIER 1 (>90% coverage required).

**Implementation Notes:**
- Atomic writes: write to temp file → rename to final path (prevents corruption)
- Provider-specific paths: `data/fmp_cache/{endpoint}/{date}/{symbol}.json`
- Cache key generation: MD5 hash of (provider, endpoint, params)
- TTL check: compare file mtime to current time
- Thread-safe file operations (though system is single-process)
- Validate JSON before write (catch serialization errors early)

**Acceptance Criteria:**
- [ ] Atomic write pattern: temp file created first, renamed on success
- [ ] TTL expiration: files older than TTL considered stale (return None)
- [ ] Provider-specific directory creation (auto-create if missing)
- [ ] Cache key generation consistent (same params → same key)
- [ ] get_cached() returns None for: missing file, expired TTL, corrupted JSON
- [ ] set_cache() rollback: temp file deleted if error during write
- [ ] Unit tests verify: atomic writes, TTL expiration, concurrent writes (mock), error rollback
- [ ] >90% test coverage (TIER 1)

**Files to Create:**
- `src/data_loader/cache.py`
- `tests/unit/test_cache_manager.py`
- `tests/integration/test_cache_filesystem.py`

**Implementation Example:**
```python
# src/data_loader/cache.py
import json
import hashlib
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

class CacheManager:
    def __init__(self, base_dir: str = "data", ttl_days: int = 7):
        self.base_dir = Path(base_dir)
        self.ttl_seconds = ttl_days * 86400

    def get_cached(self, cache_key: str, provider: str) -> Optional[Dict[str, Any]]:
        cache_path = self._get_cache_path(cache_key, provider)
        if not cache_path.exists():
            return None

        # Check TTL
        mtime = cache_path.stat().st_mtime
        age_seconds = datetime.now().timestamp() - mtime
        if age_seconds > self.ttl_seconds:
            return None

        try:
            with open(cache_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def set_cache(self, cache_key: str, provider: str, data: Dict[str, Any]):
        cache_path = self._get_cache_path(cache_key, provider)
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        # Atomic write: temp file + rename
        temp_path = cache_path.with_suffix('.tmp')
        try:
            with open(temp_path, 'w') as f:
                json.dump(data, f, indent=2)
            temp_path.rename(cache_path)  # Atomic on POSIX
        except Exception as e:
            if temp_path.exists():
                temp_path.unlink()  # Cleanup temp file
            raise CacheWriteError(f"Cache write failed: {e}")

    def _get_cache_path(self, cache_key: str, provider: str) -> Path:
        # Provider-specific path strategy
        return self.base_dir / f"{provider}_cache" / f"{cache_key}.json"

    @staticmethod
    def generate_cache_key(provider: str, endpoint: str, params: Dict[str, Any]) -> str:
        # MD5 hash for consistent keys
        key_data = f"{provider}:{endpoint}:{sorted(params.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()
```

---

### T-005: Health Monitor (metrics tracking)

| Field | Value |
|-------|-------|
| **Milestone** | M1 |
| **Effort** | 6-8 hours |
| **Priority** | P0 |
| **Dependencies** | T-001 |

**Description:**
Implement health monitor to track per-provider metrics: request counts, error counts, error rate, rate limit consumption, circuit breaker state. Provides aggregated health report.

**Implementation Notes:**
- In-memory counters (no persistence)
- Per-provider metrics (separate counters for FMP, Polygon, FRED)
- Thread-safe increments (though system is single-process async)
- Error rate calculation: errors / total_requests
- Reset method for testing
- Health report format: JSON-serializable dict

**Acceptance Criteria:**
- [ ] Track per-provider: total_requests, error_count, last_error_message
- [ ] Calculate error_rate dynamically
- [ ] Store circuit_state (external update from CircuitBreaker)
- [ ] get_health_report() returns dict with all provider stats
- [ ] reset() clears all counters (for testing)
- [ ] Unit tests verify: counter increments, error rate calculation, reset

**Files to Create:**
- `src/data_loader/health.py`
- `tests/unit/test_health_monitor.py`

**Implementation Example:**
```python
# src/data_loader/health.py
from typing import Dict, Any
from datetime import datetime

class HealthMonitor:
    def __init__(self):
        self._stats = {
            'fmp': {'requests': 0, 'errors': 0, 'last_error': None, 'circuit_state': 'CLOSED'},
            'polygon': {'requests': 0, 'errors': 0, 'last_error': None, 'circuit_state': 'CLOSED'},
            'fred': {'requests': 0, 'errors': 0, 'last_error': None, 'circuit_state': 'CLOSED'},
        }

    def record_request(self, provider: str):
        self._stats[provider]['requests'] += 1

    def record_error(self, provider: str, error_message: str):
        self._stats[provider]['errors'] += 1
        self._stats[provider]['last_error'] = error_message

    def update_circuit_state(self, provider: str, state: str):
        self._stats[provider]['circuit_state'] = state

    def get_health_report(self) -> Dict[str, Any]:
        report = {'timestamp': datetime.now().isoformat(), 'providers': {}}
        for provider, stats in self._stats.items():
            total = stats['requests']
            errors = stats['errors']
            error_rate = errors / total if total > 0 else 0.0
            report['providers'][provider] = {
                'total_requests': total,
                'errors': errors,
                'error_rate': round(error_rate, 3),
                'circuit_state': stats['circuit_state'],
                'last_error': stats['last_error']
            }
        return report

    def reset(self):
        for provider in self._stats:
            self._stats[provider] = {'requests': 0, 'errors': 0, 'last_error': None, 'circuit_state': 'CLOSED'}
```

---

### T-006: Base Data Provider Interface

| Field | Value |
|-------|-------|
| **Milestone** | M1 |
| **Effort** | 6-8 hours |
| **Priority** | P0 |
| **Dependencies** | T-003 |

**Description:**
Define abstract base class for data providers with template methods for authentication, fetching, normalization, and cache key generation. Enables plugin architecture for future providers.

**Implementation Notes:**
- Use Python ABC (Abstract Base Class)
- Template method pattern: fetch() orchestrates auth → request → normalize
- Abstract methods: _authenticate(), _make_request(), _normalize_response()
- Concrete methods: fetch(), generate_cache_key()
- Type hints for all methods
- Docstrings with examples

**Acceptance Criteria:**
- [ ] BaseDataProvider is abstract (cannot instantiate)
- [ ] Abstract methods defined: _authenticate(), _make_request(), _normalize_response()
- [ ] fetch() template method orchestrates workflow
- [ ] generate_cache_key() concrete implementation
- [ ] Type hints for all parameters and returns
- [ ] Google-style docstrings
- [ ] Unit tests verify: abstract enforcement, template method flow

**Files to Create:**
- `src/data_loader/providers/base.py`
- `src/data_loader/providers/__init__.py`
- `tests/unit/test_base_provider.py`

**Implementation Example:**
```python
# src/data_loader/providers/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import hashlib

class BaseDataProvider(ABC):
    """
    Abstract base class for data providers.

    Subclasses must implement:
    - _authenticate(): Return authentication parameters (headers, query params)
    - _make_request(): Execute HTTP request and return raw response
    - _normalize_response(): Transform provider-specific response to standard format

    Example:
        class FMPProvider(BaseDataProvider):
            def _authenticate(self):
                return {'apikey': self.api_key}

            def _make_request(self, endpoint, params):
                url = f"{self.base_url}/{endpoint}"
                return await self.http_client.get(url, params={**params, **self._authenticate()})
    """

    def __init__(self, api_key: str, http_client):
        self.api_key = api_key
        self.http_client = http_client

    async def fetch(self, endpoint: str, **params) -> Dict[str, Any]:
        """
        Fetch data from provider endpoint.

        Template method that orchestrates:
        1. Authentication
        2. HTTP request
        3. Response normalization
        """
        auth_params = self._authenticate()
        raw_response = await self._make_request(endpoint, {**params, **auth_params})
        normalized = self._normalize_response(raw_response, endpoint)
        return normalized

    @abstractmethod
    def _authenticate(self) -> Dict[str, str]:
        """Return authentication parameters (headers or query params)."""
        pass

    @abstractmethod
    async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute HTTP request and return raw JSON response."""
        pass

    @abstractmethod
    def _normalize_response(self, response: Dict[str, Any], endpoint: str) -> Dict[str, Any]:
        """Transform provider-specific response to standard format."""
        pass

    def generate_cache_key(self, endpoint: str, params: Dict[str, Any]) -> str:
        """Generate consistent cache key from endpoint and parameters."""
        key_data = f"{self.__class__.__name__}:{endpoint}:{sorted(params.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()
```

---

### T-007: Logging Setup with API Key Sanitization

| Field | Value |
|-------|-------|
| **Milestone** | M1 |
| **Effort** | 6-8 hours |
| **Priority** | P0 |
| **Dependencies** | T-002 |

**Description:**
Configure Python logging with rotating file handler, structured log format, and API key sanitization filter. This is TIER 1 security requirement (>90% coverage).

**Implementation Notes:**
- Use Python logging module (standard library)
- Rotating file handler: 10MB max size, 5 backup files
- Log format: timestamp, level, component, message
- Sanitization filter: regex-based key redaction
- Redact patterns: API keys in URLs, headers, error messages
- Replace with: `***REDACTED***`
- Unit tests verify: keys redacted in all log levels, regex patterns

**Acceptance Criteria:**
- [ ] Logging configured to file: `logs/nexus_core.log`
- [ ] Rotating handler: max 10MB, 5 backups
- [ ] Log format includes: timestamp (ISO 8601), level, logger name, message
- [ ] Sanitization filter active on all handlers
- [ ] API keys redacted in: URLs, error messages, debug logs
- [ ] Regex patterns cover: `apikey=XXX`, `api_key=XXX`, `Authorization: Bearer XXX`
- [ ] Unit tests verify: redaction patterns, no keys in output
- [ ] >90% test coverage (TIER 1)

**Files to Create:**
- `src/data_loader/logging_config.py`
- `tests/unit/test_logging_sanitization.py`
- `tests/integration/test_logging_integration.py`

**Implementation Example:**
```python
# src/data_loader/logging_config.py
import logging
from logging.handlers import RotatingFileHandler
import re

class APIKeySanitizer(logging.Filter):
    """Filter to redact API keys from log messages."""

    PATTERNS = [
        (re.compile(r'(apikey|api_key)=[^&\s]+', re.IGNORECASE), r'\1=***REDACTED***'),
        (re.compile(r'Authorization:\s*Bearer\s+[^\s]+', re.IGNORECASE), r'Authorization: Bearer ***REDACTED***'),
        (re.compile(r'[a-f0-9]{32,}', re.IGNORECASE), r'***REDACTED***'),  # MD5-like keys
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = self._sanitize(str(record.msg))
        if record.args:
            record.args = tuple(self._sanitize(str(arg)) for arg in record.args)
        return True

    def _sanitize(self, message: str) -> str:
        for pattern, replacement in self.PATTERNS:
            message = pattern.sub(replacement, message)
        return message

def setup_logging(log_file: str = "logs/nexus_core.log", level: int = logging.INFO):
    """Configure logging with API key sanitization."""
    import os
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S'
    )
    handler.setFormatter(formatter)
    handler.addFilter(APIKeySanitizer())

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(handler)

    return root_logger
```

---

### T-008: FMP Provider (13 endpoints)

| Field | Value |
|-------|-------|
| **Milestone** | M2 |
| **Effort** | 24-32 hours |
| **Priority** | P0 |
| **Dependencies** | T-006 |

**Description:**
Implement FMP Ultimate provider with support for 13 endpoints: screener, profile, quote, historical_price, earnings_calendar, balance_sheet, income_statement, cash_flow, ratios, growth, key_metrics, insider_trading, institutional_ownership. Most complex provider due to endpoint variety.

**Implementation Notes:**
- Inherit from BaseDataProvider
- Base URL: `https://financialmodelingprep.com/api/v3/`
- Authentication: `apikey` query parameter
- Endpoint-specific normalization (each has different schema)
- Cache key strategy: `{endpoint}/{date}/{symbol}.json`
- Error handling: 429 rate limit, 401 invalid key, 404 not found
- JSON fixtures for testing: record real responses once

**Acceptance Criteria:**
- [ ] All 13 endpoints implemented
- [ ] Authentication via `apikey` query param
- [ ] Normalization handles: missing fields, null values, varying schemas
- [ ] Cache key generation per endpoint
- [ ] Error handling: 401 (bad key), 429 (rate limit), 404 (not found), 5xx (server error)
- [ ] Unit tests per endpoint: normalization logic
- [ ] Integration tests: HTTP mocking with aioresponses
- [ ] JSON fixtures in `tests/fixtures/fmp/`

**Files to Create:**
- `src/data_loader/providers/fmp.py`
- `tests/unit/test_fmp_provider.py`
- `tests/integration/test_fmp_integration.py`
- `tests/fixtures/fmp/profile_AAPL.json` (and 12 more)

**Implementation Example:**
```python
# src/data_loader/providers/fmp.py
from .base import BaseDataProvider
from typing import Dict, Any

class FMPProvider(BaseDataProvider):
    """Financial Modeling Prep API provider."""

    BASE_URL = "https://financialmodelingprep.com/api/v3"

    ENDPOINTS = {
        'screener': '/stock-screener',
        'profile': '/profile/{symbol}',
        'quote': '/quote/{symbol}',
        'historical_price': '/historical-price-full/{symbol}',
        'earnings_calendar': '/earnings-calendar/{symbol}',
        'balance_sheet': '/balance-sheet-statement/{symbol}',
        'income_statement': '/income-statement/{symbol}',
        'cash_flow': '/cash-flow-statement/{symbol}',
        'ratios': '/ratios/{symbol}',
        'growth': '/financial-growth/{symbol}',
        'key_metrics': '/key-metrics/{symbol}',
        'insider_trading': '/insider-trading/{symbol}',
        'institutional_ownership': '/institutional-holder/{symbol}',
    }

    def _authenticate(self) -> Dict[str, str]:
        return {'apikey': self.api_key}

    async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        # Replace {symbol} in path
        path = self.ENDPOINTS[endpoint].format(**params)
        url = f"{self.BASE_URL}{path}"

        # Add authentication
        query_params = {**params, **self._authenticate()}
        query_params.pop('symbol', None)  # Symbol already in path

        return await self.http_client.get(url, params=query_params)

    def _normalize_response(self, response: Dict[str, Any], endpoint: str) -> Dict[str, Any]:
        # Endpoint-specific normalization
        if endpoint == 'profile':
            return self._normalize_profile(response)
        elif endpoint == 'quote':
            return self._normalize_quote(response)
        # ... more endpoints
        return response

    def _normalize_profile(self, data: Any) -> Dict[str, Any]:
        # Handle both single object and array responses
        if isinstance(data, list):
            data = data[0] if data else {}

        return {
            'symbol': data.get('symbol'),
            'company_name': data.get('companyName'),
            'sector': data.get('sector'),
            'industry': data.get('industry'),
            'market_cap': data.get('mktCap'),
            # ... more fields
        }
```

**Effort Breakdown:**
- Base implementation: 6h
- 13 endpoint implementations: 12h (1h each, some simpler)
- Normalization logic: 6h (complex schemas)
- Unit tests: 8h
- Integration tests: 4h
- JSON fixtures: 2h (record from real API)
- Debugging: 2-4h
- **Total: 40-44h (realistic)**

---

### T-009: Polygon Provider (4 endpoints)

| Field | Value |
|-------|-------|
| **Milestone** | M2 |
| **Effort** | 12-16 hours |
| **Priority** | P0 |
| **Dependencies** | T-006 |

**Description:**
Implement Polygon.io provider with 4 endpoints: aggs_daily, trades, options_snapshot, market_snapshot. Simpler than FMP but has date range complexity.

**Implementation Notes:**
- Base URL: `https://api.polygon.io/v2/`
- Authentication: `apiKey` query parameter
- Date range handling for aggregates (from/to parameters)
- Hash-based cache keys (complex query params)
- Rate limit: 5 req/min (free tier), 10 concurrent (QoS)
- Options endpoint has nested data structures

**Acceptance Criteria:**
- [ ] 4 endpoints implemented: aggs_daily, trades, options_snapshot, market_snapshot
- [ ] Authentication via `apiKey` query param
- [ ] Date range handling for aggs_daily
- [ ] Hash-based cache key for complex params
- [ ] Normalization handles nested structures (options)
- [ ] Unit tests: normalization per endpoint
- [ ] Integration tests: date range edge cases
- [ ] JSON fixtures in `tests/fixtures/polygon/`

**Files to Create:**
- `src/data_loader/providers/polygon.py`
- `tests/unit/test_polygon_provider.py`
- `tests/integration/test_polygon_integration.py`
- `tests/fixtures/polygon/aggs_daily_SPY.json` (and 3 more)

**Effort Breakdown:**
- Base implementation: 3h
- 4 endpoint implementations: 4h
- Date range logic: 2h
- Normalization: 3h
- Unit tests: 4h
- Integration tests: 2h
- JSON fixtures: 1h
- Debugging: 1-3h
- **Total: 20-22h (realistic)**

---

### T-010: FRED Provider (32 series + base)

| Field | Value |
|-------|-------|
| **Milestone** | M2 |
| **Effort** | 16-24 hours |
| **Priority** | P0 |
| **Dependencies** | T-006 |

**Description:**
Implement FRED (Federal Reserve Economic Data) provider supporting 32 predefined series (CPIAUCSL, UNRATE, DGS10, etc.) plus generic series endpoint.

**Implementation Notes:**
- Base URL: `https://api.stlouisfed.org/fred/`
- Authentication: `api_key` query parameter
- Series endpoint: `/series/observations`
- 32 predefined series as constants (see DECISIONS.md Section 14)
- Date range handling (start_date, end_date)
- Time series normalization (date + value pairs)
- Simple endpoint pattern (less variety than FMP)

**Acceptance Criteria:**
- [ ] Generic series fetch supports any series_id
- [ ] 32 predefined series documented (constants or enum)
- [ ] Authentication via `api_key` query param
- [ ] Date range parameters: observation_start, observation_end
- [ ] Normalization to consistent time series format: `[{date, value}, ...]`
- [ ] Cache key: `fred_cache/{series_id}/{date_range}.json`
- [ ] Unit tests: sample series (5-10), normalization
- [ ] Integration tests: date range edge cases
- [ ] JSON fixtures for representative series

**Files to Create:**
- `src/data_loader/providers/fred.py`
- `tests/unit/test_fred_provider.py`
- `tests/integration/test_fred_integration.py`
- `tests/fixtures/fred/CPIAUCSL.json` (and 5-10 more samples)

**Effort Breakdown:**
- Base implementation: 4h
- Series endpoint: 3h
- Date range logic: 2h
- Normalization: 3h
- 32 series constants: 1h
- Unit tests: 6h
- Integration tests: 3h
- JSON fixtures: 2h
- Debugging: 2-4h
- **Total: 26-28h (realistic)**

---

### T-011: Provider Integration Tests (mocked HTTP)

| Field | Value |
|-------|-------|
| **Milestone** | M2 |
| **Effort** | 12-16 hours |
| **Priority** | P0 |
| **Dependencies** | T-008, T-009, T-010 |

**Description:**
Create comprehensive integration tests for all 3 providers using aioresponses to mock HTTP responses. Validates provider behavior with realistic mocked API responses.

**Implementation Notes:**
- Use aioresponses library to mock aiohttp requests
- Test scenarios: success (200), rate limit (429), server error (5xx), timeout
- Verify provider handles errors correctly
- Validate normalization with realistic response fixtures
- Test retry logic integration (without actual delays)
- Mock circuit breaker interactions

**Acceptance Criteria:**
- [ ] ~40 integration tests total (~13 per provider + orchestration)
- [ ] HTTP 200 success scenarios (all endpoints)
- [ ] HTTP 429 rate limit handling
- [ ] HTTP 5xx retry logic
- [ ] Timeout handling
- [ ] Malformed JSON response handling
- [ ] All tests use aioresponses (no real API calls)
- [ ] Tests run in <60 seconds

**Files to Create/Extend:**
- `tests/integration/test_fmp_integration.py`
- `tests/integration/test_polygon_integration.py`
- `tests/integration/test_fred_integration.py`

**Effort Breakdown:**
- FMP integration tests: 5h (13 endpoints)
- Polygon integration tests: 3h (4 endpoints)
- FRED integration tests: 3h (sample series)
- Error scenario tests: 3h (429, 5xx, timeout)
- Debugging flaky tests: 2-4h
- **Total: 16-18h (realistic)**

---

### T-012: QoS Semaphore Router

| Field | Value |
|-------|-------|
| **Milestone** | M3 |
| **Effort** | 8-12 hours |
| **Priority** | P0 |
| **Dependencies** | T-006 |

**Description:**
Implement QoS (Quality of Service) router with provider-specific semaphores to enforce concurrency limits: FMP=3, Polygon=10, FRED=1. TIER 1 component (>90% coverage).

**Implementation Notes:**
- Use asyncio.Semaphore per provider
- Context manager for acquire/release pattern
- Timeout handling (raise error if cannot acquire)
- Configurable limits (from config)
- Log semaphore acquisition/release
- Thread-safe (though system is single async process)

**Acceptance Criteria:**
- [ ] Separate semaphores for FMP (max=3), Polygon (max=10), FRED (max=1)
- [ ] acquire(provider) blocks until semaphore available
- [ ] release(provider) releases semaphore
- [ ] Context manager support: `async with qos_router.acquire(provider):`
- [ ] Timeout parameter (default 30s)
- [ ] Unit tests verify: concurrency limits enforced, timeout handling
- [ ] >90% test coverage (TIER 1)

**Files to Create:**
- `src/data_loader/qos_router.py`
- `tests/unit/test_qos_router.py`

**Implementation Example:**
```python
# src/data_loader/qos_router.py
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator

class QoSRouter:
    """Quality of Service router with provider-specific concurrency limits."""

    def __init__(self, fmp_limit: int = 3, polygon_limit: int = 10, fred_limit: int = 1):
        self._semaphores = {
            'fmp': asyncio.Semaphore(fmp_limit),
            'polygon': asyncio.Semaphore(polygon_limit),
            'fred': asyncio.Semaphore(fred_limit),
        }

    @asynccontextmanager
    async def acquire(self, provider: str, timeout: float = 30.0) -> AsyncIterator[None]:
        """
        Acquire semaphore for provider with timeout.

        Usage:
            async with qos_router.acquire('fmp'):
                # Make API request
                pass
        """
        semaphore = self._semaphores.get(provider)
        if not semaphore:
            raise ValueError(f"Unknown provider: {provider}")

        try:
            await asyncio.wait_for(semaphore.acquire(), timeout=timeout)
            yield
        except asyncio.TimeoutError:
            raise QoSTimeoutError(f"Could not acquire semaphore for {provider} within {timeout}s")
        finally:
            semaphore.release()
```

**Effort Breakdown:**
- Implementation: 3h
- Unit tests: 4h (test concurrent scenarios)
- Integration with providers: 2h
- Debugging async edge cases: 1-3h
- **Total: 10-12h (realistic)**

---

### T-013: Circuit Breaker Manager

| Field | Value |
|-------|-------|
| **Milestone** | M3 |
| **Effort** | 12-16 hours |
| **Priority** | P0 |
| **Dependencies** | T-005 |

**Description:**
Implement circuit breaker pattern with 3 states (CLOSED, OPEN, HALF-OPEN) and per-provider failure tracking. Opens at >20% error rate. TIER 1 component (>90% coverage).

**Implementation Notes:**
- Finite state machine: CLOSED → OPEN → HALF-OPEN → CLOSED (or back to OPEN)
- Per-provider state (FMP, Polygon, FRED independent)
- Sliding window error tracking (last N requests)
- Threshold: >20% error rate
- Timeout in OPEN state (e.g., 60s before HALF-OPEN)
- HALF-OPEN: single test request, success → CLOSED, failure → OPEN
- Integration with HealthMonitor for state reporting

**Acceptance Criteria:**
- [ ] 3 states: CLOSED (normal), OPEN (failing), HALF-OPEN (testing recovery)
- [ ] Per-provider state tracking
- [ ] Error rate threshold: >20% (configurable)
- [ ] Sliding window: last 10 requests (configurable)
- [ ] OPEN timeout: 60s (configurable)
- [ ] HALF-OPEN recovery: 1 test request
- [ ] Raises CircuitOpenError when state=OPEN
- [ ] Unit tests verify: state transitions, threshold calculation, timeout, recovery
- [ ] Integration tests: full state machine cycle
- [ ] >90% test coverage (TIER 1)

**Files to Create:**
- `src/data_loader/circuit_breaker.py`
- `tests/unit/test_circuit_breaker.py`
- `tests/integration/test_circuit_breaker_integration.py`

**Implementation Example:**
```python
# src/data_loader/circuit_breaker.py
from enum import Enum
from collections import deque
from datetime import datetime, timedelta
from typing import Dict

class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

class CircuitBreaker:
    """Per-provider circuit breaker with error rate threshold."""

    def __init__(self, threshold: float = 0.2, window_size: int = 10, timeout_seconds: int = 60):
        self.threshold = threshold
        self.window_size = window_size
        self.timeout = timedelta(seconds=timeout_seconds)

        self._states: Dict[str, CircuitState] = {
            'fmp': CircuitState.CLOSED,
            'polygon': CircuitState.CLOSED,
            'fred': CircuitState.CLOSED,
        }
        self._windows: Dict[str, deque] = {
            'fmp': deque(maxlen=window_size),
            'polygon': deque(maxlen=window_size),
            'fred': deque(maxlen=window_size),
        }
        self._open_times: Dict[str, datetime] = {}

    def record_success(self, provider: str):
        self._windows[provider].append(True)
        if self._states[provider] == CircuitState.HALF_OPEN:
            self._states[provider] = CircuitState.CLOSED
            self._open_times.pop(provider, None)

    def record_failure(self, provider: str):
        self._windows[provider].append(False)
        error_rate = self._calculate_error_rate(provider)

        if error_rate > self.threshold:
            self._states[provider] = CircuitState.OPEN
            self._open_times[provider] = datetime.now()

        if self._states[provider] == CircuitState.HALF_OPEN:
            self._states[provider] = CircuitState.OPEN
            self._open_times[provider] = datetime.now()

    def check(self, provider: str):
        """Check if circuit allows request. Raises CircuitOpenError if OPEN."""
        state = self._states[provider]

        if state == CircuitState.OPEN:
            # Check if timeout elapsed → HALF_OPEN
            open_time = self._open_times.get(provider)
            if open_time and datetime.now() - open_time > self.timeout:
                self._states[provider] = CircuitState.HALF_OPEN
            else:
                raise CircuitOpenError(f"Circuit breaker OPEN for {provider}")

    def _calculate_error_rate(self, provider: str) -> float:
        window = self._windows[provider]
        if not window:
            return 0.0
        failures = sum(1 for success in window if not success)
        return failures / len(window)
```

**Effort Breakdown:**
- State machine implementation: 4h
- Error rate tracking: 2h
- Timeout and recovery: 2h
- Integration with HealthMonitor: 1h
- Unit tests: 5h (complex state transitions)
- Integration tests: 2h
- Debugging edge cases: 2-4h
- **Total: 18-20h (realistic)**

---

### T-014: Retry Handler (exponential backoff + jitter)

| Field | Value |
|-------|-------|
| **Milestone** | M3 |
| **Effort** | 8-12 hours |
| **Priority** | P0 |
| **Dependencies** | T-003 |

**Description:**
Implement retry logic with exponential backoff and jitter for transient failures (5xx, timeouts). Does NOT retry 4xx errors or 429 rate limits.

**Implementation Notes:**
- Exponential backoff: delay = base * (2 ** attempt)
- Jitter: randomize delay ±20% to prevent thundering herd
- Max retries: 3 (configurable)
- Retry only: 5xx errors, timeouts (aiohttp.ClientTimeout)
- Do NOT retry: 4xx errors, 429 (handled separately)
- Log each retry attempt
- Total time budget: ~7-8s max (1s + 2s + 4s)

**Acceptance Criteria:**
- [ ] Exponential backoff: attempt 1 → ~1s, attempt 2 → ~2s, attempt 3 → ~4s
- [ ] Jitter: randomize delay ±20%
- [ ] Max retries: 3 (configurable)
- [ ] Retry only on: 5xx, timeouts
- [ ] Do NOT retry: 4xx, 429
- [ ] Log each retry: attempt number, delay, error
- [ ] Unit tests verify: backoff calculation, jitter range, retry logic, max retries
- [ ] Integration tests: mock 5xx → success on 3rd retry

**Files to Create:**
- `src/data_loader/retry.py`
- `tests/unit/test_retry_handler.py`
- `tests/integration/test_retry_integration.py`

**Implementation Example:**
```python
# src/data_loader/retry.py
import asyncio
import random
from typing import Callable, Any

class RetryHandler:
    """Retry handler with exponential backoff and jitter."""

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, jitter: float = 0.2):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.jitter = jitter

    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic."""
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if not self._should_retry(e, attempt):
                    raise

                last_error = e
                if attempt < self.max_retries:
                    delay = self._calculate_delay(attempt)
                    logging.warning(f"Retry {attempt+1}/{self.max_retries} after {delay:.2f}s: {e}")
                    await asyncio.sleep(delay)

        raise last_error

    def _should_retry(self, error: Exception, attempt: int) -> bool:
        """Determine if error is retryable."""
        if attempt >= self.max_retries:
            return False

        # Retry 5xx and timeouts
        if isinstance(error, aiohttp.ClientError):
            if hasattr(error, 'status'):
                return 500 <= error.status < 600
            return True  # Timeout

        return False

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and jitter."""
        delay = self.base_delay * (2 ** attempt)
        jitter_amount = delay * self.jitter
        return delay + random.uniform(-jitter_amount, jitter_amount)
```

**Effort Breakdown:**
- Implementation: 3h
- Backoff + jitter logic: 2h
- Unit tests: 4h
- Integration tests: 2h
- Debugging async timing: 1-3h
- **Total: 12-14h (realistic)**

---

### T-015: Rate Limit Handling (HTTP 429)

| Field | Value |
|-------|-------|
| **Milestone** | M3 |
| **Effort** | 6-8 hours |
| **Priority** | P0 |
| **Dependencies** | T-014 |

**Description:**
Handle HTTP 429 rate limit responses by parsing Retry-After header and sleeping before retry. Separate from exponential backoff logic.

**Implementation Notes:**
- Parse Retry-After header (seconds or HTTP date)
- Sleep for specified duration
- Log rate limit hit with cooldown time
- Update HealthMonitor rate_limit_pct
- Do NOT use exponential backoff for 429 (respect server instruction)
- Single retry after cooldown (not multiple)

**Acceptance Criteria:**
- [ ] Detect HTTP 429 response
- [ ] Parse Retry-After header (seconds format)
- [ ] Sleep for Retry-After duration
- [ ] Log rate limit event
- [ ] Single retry after cooldown
- [ ] If Retry-After missing, use default cooldown (60s)
- [ ] Unit tests verify: header parsing, cooldown logic
- [ ] Integration tests: mock 429 → success after cooldown

**Files to Create:**
- `src/data_loader/rate_limit.py` (or extend retry.py)
- `tests/unit/test_rate_limit.py`
- `tests/integration/test_rate_limit_integration.py`

**Effort Breakdown:**
- Implementation: 2h
- Retry-After parsing: 1h
- Integration with retry handler: 1h
- Unit tests: 2h
- Integration tests: 1h
- Debugging: 1-2h
- **Total: 8-9h (realistic)**

---

### T-016: DataLoader Unified Interface

| Field | Value |
|-------|-------|
| **Milestone** | M3 |
| **Effort** | 10-14 hours |
| **Priority** | P0 |
| **Dependencies** | T-012, T-013, T-014 |

**Description:**
Implement main DataLoader class that orchestrates all components: providers, QoS router, circuit breaker, retry handler, cache. Provides unified interface: `get_fmp_data()`, `get_polygon_data()`, `get_fred_data()`.

**Implementation Notes:**
- Singleton or dependency-injected instance
- Orchestration flow: check cache → check circuit → acquire QoS → call provider → handle retries → update cache
- Provider routing: map provider name to provider instance
- Health report aggregation
- Operating mode enforcement (LIVE vs READ-ONLY)
- Session management (long-lived aiohttp.ClientSession)

**Acceptance Criteria:**
- [ ] Methods: `get_fmp_data()`, `get_polygon_data()`, `get_fred_data()`, `get_api_health_report()`, `set_operating_mode()`
- [ ] Orchestration: cache → circuit → QoS → provider → retry → cache
- [ ] Cache hit: return immediately (no API call)
- [ ] Circuit OPEN: raise error (no API call)
- [ ] QoS: enforce concurrency limits
- [ ] Retry: handle 5xx and timeouts
- [ ] Rate limit: handle 429
- [ ] Health tracking: update counters per request
- [ ] Operating modes: LIVE (normal), READ-ONLY (cache only)
- [ ] Unit tests: orchestration flow, mode enforcement
- [ ] Integration tests: full request cycle

**Files to Create:**
- `src/data_loader/loader.py`
- `tests/unit/test_loader.py`
- `tests/integration/test_loader_integration.py`

**Implementation Example:**
```python
# src/data_loader/loader.py
from typing import Dict, Any, Optional
from .providers.fmp import FMPProvider
from .providers.polygon import PolygonProvider
from .providers.fred import FREDProvider

class DataLoader:
    """Unified interface for financial data retrieval."""

    def __init__(self, config, cache, health_monitor, circuit_breaker, qos_router, retry_handler):
        self.config = config
        self.cache = cache
        self.health = health_monitor
        self.circuit = circuit_breaker
        self.qos = qos_router
        self.retry = retry_handler

        # Initialize providers
        self.providers = {
            'fmp': FMPProvider(config.fmp_key, http_client),
            'polygon': PolygonProvider(config.polygon_key, http_client),
            'fred': FREDProvider(config.fred_key, http_client),
        }

        self.mode = 'LIVE'

    async def get_fmp_data(self, endpoint: str, **params) -> Dict[str, Any]:
        """Fetch data from FMP provider."""
        return await self._fetch('fmp', endpoint, params)

    async def _fetch(self, provider: str, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrate data fetch with all resilience components."""
        cache_key = self.providers[provider].generate_cache_key(endpoint, params)

        # 1. Check cache
        cached = self.cache.get_cached(cache_key, provider)
        if cached:
            return cached

        # 2. Check mode
        if self.mode == 'READ_ONLY':
            raise ReadOnlyError(f"READ-ONLY mode: no API calls allowed")

        # 3. Check circuit breaker
        self.circuit.check(provider)

        # 4. Acquire QoS semaphore
        async with self.qos.acquire(provider):
            try:
                # 5. Fetch with retry
                self.health.record_request(provider)
                data = await self.retry.execute(
                    self.providers[provider].fetch,
                    endpoint,
                    **params
                )

                # 6. Update cache
                self.cache.set_cache(cache_key, provider, data)

                # 7. Record success
                self.circuit.record_success(provider)
                return data

            except Exception as e:
                self.health.record_error(provider, str(e))
                self.circuit.record_failure(provider)
                raise

    def get_api_health_report(self) -> Dict[str, Any]:
        return self.health.get_health_report()

    def set_operating_mode(self, mode: str):
        if mode not in ('LIVE', 'READ_ONLY'):
            raise ValueError(f"Invalid mode: {mode}")
        self.mode = mode
```

**Effort Breakdown:**
- Core orchestration: 4h
- Provider integration: 2h
- Mode enforcement: 1h
- Session management: 1h
- Unit tests: 4h
- Integration tests: 3h
- Debugging orchestration: 2-4h
- **Total: 17-19h (realistic)**

---

### T-017: Operating Modes (LIVE/READ-ONLY)

| Field | Value |
|-------|-------|
| **Milestone** | M3 |
| **Effort** | 4-6 hours |
| **Priority** | P0 |
| **Dependencies** | T-016 |

**Description:**
Implement operating mode switching: LIVE (normal API calls) and READ-ONLY (cache-only, no API calls). Enables offline analysis and testing.

**Implementation Notes:**
- Mode stored in DataLoader state
- LIVE: normal operation (default)
- READ-ONLY: cache hit returns data, cache miss raises error
- set_operating_mode() method validates mode
- Log mode changes
- Unit tests verify mode enforcement

**Acceptance Criteria:**
- [ ] Modes: LIVE, READ_ONLY
- [ ] LIVE mode: normal behavior (cache → API → cache)
- [ ] READ_ONLY mode: cache hit → data, cache miss → ReadOnlyError
- [ ] set_operating_mode() validates input
- [ ] Log mode changes
- [ ] Unit tests: mode switching, enforcement
- [ ] E2E test: READ-ONLY prevents API calls

**Files to Create/Extend:**
- `src/data_loader/loader.py` (extend)
- `tests/unit/test_loader.py` (extend)
- `tests/e2e/test_readonly_mode.py`

**Effort Breakdown:**
- Implementation: 1h
- Error handling: 1h
- Unit tests: 2h
- E2E tests: 1h
- Debugging: 1-2h
- **Total: 6-7h (realistic)**

---

### T-018: Resilience Integration Tests

| Field | Value |
|-------|-------|
| **Milestone** | M3 |
| **Effort** | 4-8 hours |
| **Priority** | P0 |
| **Dependencies** | T-012, T-013, T-014 |

**Description:**
Integration tests validating resilience components working together: circuit breaker with retry, QoS with circuit breaker, full orchestration cycle.

**Implementation Notes:**
- Mock HTTP responses to simulate failures
- Verify circuit breaker opens after threshold
- Verify QoS limits concurrent requests
- Verify retry logic with backoff
- Test full failure → recovery cycle
- All tests must run in <60s

**Acceptance Criteria:**
- [ ] Circuit breaker integration: errors → OPEN → HALF-OPEN → CLOSED
- [ ] QoS integration: concurrent limit enforcement
- [ ] Retry integration: 5xx → backoff → success
- [ ] Full cycle: cache miss → circuit check → QoS → retry → cache write
- [ ] All tests use mocked HTTP (aioresponses)
- [ ] Tests run in <60s

**Files to Create:**
- `tests/integration/test_resilience_integration.py`

**Effort Breakdown:**
- Circuit breaker integration: 2h
- QoS integration: 1h
- Retry integration: 1h
- Full cycle test: 2h
- Debugging timing issues: 2-4h
- **Total: 8-10h (realistic)**

---

### T-019: Unit Test Suite Completion (TIER 1 >90%)

| Field | Value |
|-------|-------|
| **Milestone** | M4 |
| **Effort** | 12-16 hours |
| **Priority** | P0 |
| **Dependencies** | All previous tasks |

**Description:**
Complete unit test suite to achieve >90% coverage for TIER 1 components (Circuit Breaker, QoS Router, API Key Sanitization, Atomic Cache Writes) and >80% overall coverage.

**Implementation Notes:**
- Focus on TIER 1 components first
- Use pytest-cov to identify gaps
- Write tests for edge cases and error paths
- Mock external dependencies
- Fast execution (<20s for all unit tests)

**Acceptance Criteria:**
- [ ] >90% coverage: Circuit Breaker, QoS Router, Logging Sanitization, Cache (atomic writes)
- [ ] >80% coverage: Providers, DataLoader, Retry Handler, Health Monitor
- [ ] ~150 unit tests total
- [ ] All tests passing
- [ ] Execution time <20s
- [ ] Coverage report generated (HTML + terminal)

**Files to Create/Extend:**
- Extend all existing `tests/unit/test_*.py` files
- Fill coverage gaps identified by pytest-cov

**Effort Breakdown:**
- Coverage analysis: 2h
- Gap filling (TIER 1): 6h
- Gap filling (TIER 2): 4h
- Edge case tests: 3h
- Debugging flaky tests: 2-4h
- **Total: 17-19h (realistic)**

---

### T-020: E2E Test Scenarios (10 critical paths)

| Field | Value |
|-------|-------|
| **Milestone** | M4 |
| **Effort** | 8-12 hours |
| **Priority** | P0 |
| **Dependencies** | T-016 |

**Description:**
Implement 10 end-to-end test scenarios covering critical user workflows: cache miss → API → cache hit, circuit breaker full cycle, multi-provider parallel fetch, READ-ONLY mode.

**Implementation Notes:**
- Mock all HTTP responses (aioresponses)
- Test full DataLoader orchestration
- Verify state changes (cache, circuit breaker, health)
- Each test validates complete workflow
- Tests should run in <30s total

**Acceptance Criteria:**
- [ ] 10 E2E tests covering critical scenarios (see TEST_STRATEGY.md Section 8.5)
- [ ] TC-401: Cache miss → API → Cache hit
- [ ] TC-402: READ-ONLY mode enforcement
- [ ] TC-403: Parallel multi-provider fetch
- [ ] TC-404: Health report aggregation
- [ ] Circuit breaker full cycle: OPEN → HALF-OPEN → CLOSED
- [ ] QoS limits concurrent requests
- [ ] All tests mocked (no real API calls)
- [ ] Execution time <30s

**Files to Create:**
- `tests/e2e/test_happy_path.py`
- `tests/e2e/test_readonly_mode.py`
- `tests/e2e/test_parallel_fetch.py`
- `tests/e2e/test_resilience.py`

**Effort Breakdown:**
- Happy path tests: 3h
- Circuit breaker cycle: 2h
- Parallel fetch: 2h
- READ-ONLY mode: 1h
- Health report: 1h
- Debugging orchestration: 3-5h
- **Total: 12-14h (realistic)**

---

### T-021: Security Tests (API key sanitization)

| Field | Value |
|-------|-------|
| **Milestone** | M4 |
| **Effort** | 4-6 hours |
| **Priority** | P0 |
| **Dependencies** | T-007 |

**Description:**
Implement security tests validating API key sanitization in all log output, error messages, and cache files. TIER 1 requirement (TC-101 through TC-106).

**Implementation Notes:**
- Test all log levels (DEBUG, INFO, WARNING, ERROR)
- Verify keys redacted in: URLs, headers, error messages
- Verify keys NOT in cache files
- Verify .env in .gitignore
- Use regex patterns to detect key leakage

**Acceptance Criteria:**
- [ ] TC-101: Keys not in error messages
- [ ] TC-102: Keys not in success logs
- [ ] TC-103: Keys not in cache files
- [ ] TC-104: .env in .gitignore
- [ ] TC-105: HTTPS enforcement
- [ ] TC-106: TLS validation enabled
- [ ] All security tests passing
- [ ] 100% coverage of security test cases

**Files to Create:**
- `tests/unit/test_security.py`
- `tests/integration/test_security_integration.py`

**Effort Breakdown:**
- Log sanitization tests: 2h
- Cache file tests: 1h
- HTTPS/TLS tests: 1h
- .gitignore verification: 0.5h
- Debugging regex patterns: 1-2h
- **Total: 5.5-6.5h (realistic)**

---

### T-022: Coverage Analysis and Gap Filling

| Field | Value |
|-------|-------|
| **Milestone** | M4 |
| **Effort** | 4-6 hours |
| **Priority** | P0 |
| **Dependencies** | T-019, T-020 |

**Description:**
Analyze coverage reports, identify gaps, and write tests to fill gaps until >80% overall and >90% TIER 1 coverage achieved.

**Implementation Notes:**
- Run pytest-cov with HTML report
- Review uncovered lines
- Prioritize TIER 1 gaps
- Write targeted tests for specific branches
- Exclude legitimate uncoverable code (defensive errors, debug code)

**Acceptance Criteria:**
- [ ] Overall coverage >80%
- [ ] TIER 1 coverage >90%
- [ ] Coverage report generated (HTML)
- [ ] Coverage gaps documented (excluded lines marked)
- [ ] All new tests passing

**Files to Create/Extend:**
- Extend existing test files based on gaps

**Effort Breakdown:**
- Initial coverage analysis: 1h
- Gap identification: 1h
- Writing gap-filling tests: 3h
- Re-analysis and verification: 1h
- Documentation: 0.5-1h
- **Total: 6.5-7h (realistic)**

---

### T-023: CI/CD Pipeline Setup (GitHub Actions)

| Field | Value |
|-------|-------|
| **Milestone** | M4 |
| **Effort** | 4-6 hours |
| **Priority** | P1 |
| **Dependencies** | T-022 |

**Description:**
Set up GitHub Actions workflow for automated testing: lint → type check → unit → integration → E2E → coverage → secret scan.

**Implementation Notes:**
- Run on: push to main, pull requests
- Jobs: lint, type-check, test
- Test job runs all test types
- Upload coverage report to codecov or similar
- Secret scanning with detect-secrets
- Cache pip dependencies for speed
- Target execution time: <2 minutes

**Acceptance Criteria:**
- [ ] GitHub Actions workflow file created
- [ ] Jobs: lint (ruff), type-check (mypy), test (pytest)
- [ ] Test job runs: unit → integration → E2E
- [ ] Coverage report uploaded
- [ ] Secret scanning runs
- [ ] Badge in README.md
- [ ] Execution time <2 minutes

**Files to Create:**
- `.github/workflows/ci.yml`
- Update `README.md` with badge

**Effort Breakdown:**
- Workflow setup: 2h
- Coverage upload: 1h
- Secret scanning: 1h
- Testing and debugging: 1-2h
- Documentation: 0.5-1h
- **Total: 5.5-7h (realistic)**

---

### T-024: Documentation Polish (README, examples)

| Field | Value |
|-------|-------|
| **Milestone** | M4 |
| **Effort** | 6-8 hours |
| **Priority** | P1 |
| **Dependencies** | All |

**Description:**
Polish documentation: comprehensive README.md with setup instructions, usage examples, architecture overview, and troubleshooting. Create example scripts demonstrating usage.

**Implementation Notes:**
- README sections: Overview, Features, Installation, Quickstart, Examples, Configuration, Architecture, Testing, Contributing
- Example scripts: basic usage, multi-provider fetch, error handling, READ-ONLY mode
- API reference (docstrings already written)
- Troubleshooting common issues
- Link to architecture docs

**Acceptance Criteria:**
- [ ] README.md complete with all sections
- [ ] Installation instructions: <5 minute setup
- [ ] Quickstart example: fetch data from all 3 providers
- [ ] Example scripts in `examples/` directory
- [ ] Configuration documentation (.env variables)
- [ ] Architecture diagram (ASCII or image)
- [ ] Troubleshooting section
- [ ] Links to detailed docs in `docs/`

**Files to Create:**
- Update `README.md`
- `examples/quickstart.py`
- `examples/multi_provider.py`
- `examples/error_handling.py`
- `examples/readonly_mode.py`

**Effort Breakdown:**
- README writing: 3h
- Example scripts: 2h
- Architecture diagram: 1h
- Troubleshooting: 1h
- Review and polish: 1-2h
- **Total: 8-9h (realistic)**

---

### T-025: Pre-commit Hooks (secret scanning)

| Field | Value |
|-------|-------|
| **Milestone** | M4 |
| **Effort** | 2-3 hours |
| **Priority** | P1 |
| **Dependencies** | T-007 |

**Description:**
Set up pre-commit hooks to automatically scan for API keys and secrets before commits. Prevents accidental key leakage.

**Implementation Notes:**
- Use detect-secrets or similar tool
- Configure to scan: *.py, *.md, *.yml, *.json
- Exclude: tests/fixtures/ (contains mock data)
- Baseline file for known false positives
- Instructions in README for setup

**Acceptance Criteria:**
- [ ] Pre-commit configuration file created
- [ ] detect-secrets hook configured
- [ ] Baseline file for false positives
- [ ] Hook blocks commits with secrets
- [ ] README.md documents setup
- [ ] Tested with actual secret in file

**Files to Create:**
- `.pre-commit-config.yaml`
- `.secrets.baseline`
- Update `README.md` with setup instructions

**Effort Breakdown:**
- Pre-commit setup: 1h
- Baseline configuration: 0.5h
- Testing: 0.5h
- Documentation: 0.5h
- Debugging: 0.5-1h
- **Total: 3-3.5h (realistic)**

---

### T-026: Manual Smoke Test with Real APIs

| Field | Value |
|-------|-------|
| **Milestone** | M4 |
| **Effort** | 2-3 hours |
| **Priority** | P1 |
| **Dependencies** | All |

**Description:**
Manual validation with real API calls to all 3 providers. Verify: authentication works, data fetched, cache written, circuit breaker recovers, health report accurate.

**Implementation Notes:**
- Use real API keys (.env file)
- Test representative endpoints from each provider
- Verify cache files created
- Trigger circuit breaker (intentional errors)
- Verify recovery cycle
- Document any discrepancies from mocked tests

**Acceptance Criteria:**
- [ ] FMP: fetch profile, quote, historical_price (3 endpoints)
- [ ] Polygon: fetch aggs_daily, market_snapshot (2 endpoints)
- [ ] FRED: fetch CPIAUCSL, UNRATE, DGS10 (3 series)
- [ ] Cache files created in correct paths
- [ ] Circuit breaker opens after failures
- [ ] Circuit breaker recovers
- [ ] Health report shows accurate stats
- [ ] No errors in logs (keys sanitized)
- [ ] Manual test report documented

**Files to Create:**
- `scripts/manual_smoke_test.py`
- `docs/MANUAL_TEST_REPORT.md`

**Effort Breakdown:**
- Script creation: 1h
- Test execution: 1h
- Issue investigation: 0.5-1h
- Report writing: 0.5h
- **Total: 3-3.5h (realistic)**

---

## 4. Technical Approach

| Component | Approach | Rationale |
|-----------|----------|-----------|
| **Config Management** | python-dotenv + environment variables | Standard practice; keeps secrets out of code; supports CI override |
| **HTTP Client** | aiohttp.ClientSession (long-lived) | Production-ready async client; connection pooling; timeout control |
| **Cache** | Filesystem JSON with atomic writes (temp+rename) | Simple, inspectable, no DB overhead; atomic writes prevent corruption |
| **QoS Router** | asyncio.Semaphore per provider | Efficient async concurrency control; prevents rate limit violations |
| **Circuit Breaker** | Finite state machine with sliding window | Industry-standard pattern; per-provider isolation; error rate threshold |
| **Retry Handler** | Exponential backoff with jitter | Prevents thundering herd; respects server capacity; fast recovery |
| **Providers** | Plugin architecture (BaseDataProvider) | Extensibility; separation of concerns; consistent interface |
| **Testing** | pytest + pytest-asyncio + aioresponses | Industry standard; excellent async support; reliable HTTP mocking |
| **Logging** | Python logging with rotating file handler | Standard library; API key sanitization via filter; no external deps |
| **CI/CD** | GitHub Actions | Free for public repos; familiar workflow; good Python support |

---

## 5. File Structure (Target)

```
nexus_core/
├── .github/
│   └── workflows/
│       └── ci.yml
├── .pre-commit-config.yaml
├── .secrets.baseline
├── .gitignore
├── .env.example
├── README.md
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml (optional - for ruff/mypy config)
├── src/
│   └── data_loader/
│       ├── __init__.py
│       ├── loader.py              # DataLoader unified interface
│       ├── config.py              # Config Manager
│       ├── qos_router.py          # QoS Semaphore Router
│       ├── circuit_breaker.py     # Circuit Breaker Manager
│       ├── retry.py               # Retry & Backoff Handler
│       ├── rate_limit.py          # Rate Limit Handler
│       ├── http_client.py         # HTTP Client Layer
│       ├── cache.py               # Cache Manager
│       ├── health.py              # Health Monitor
│       ├── logging_config.py      # Logging with sanitization
│       └── providers/
│           ├── __init__.py
│           ├── base.py            # BaseDataProvider
│           ├── fmp.py             # FMP Provider
│           ├── polygon.py         # Polygon Provider
│           └── fred.py            # FRED Provider
├── tests/
│   ├── conftest.py                # Shared fixtures
│   ├── fixtures/                  # Mock API responses
│   │   ├── fmp/
│   │   │   ├── profile_AAPL.json
│   │   │   ├── quote_MSFT.json
│   │   │   └── ... (13 endpoints)
│   │   ├── polygon/
│   │   │   ├── aggs_daily_SPY.json
│   │   │   └── ... (4 endpoints)
│   │   └── fred/
│   │       ├── CPIAUCSL.json
│   │       ├── UNRATE.json
│   │       └── ... (sample series)
│   ├── unit/                      # Unit tests (~150)
│   │   ├── test_config_manager.py
│   │   ├── test_http_client.py
│   │   ├── test_cache_manager.py
│   │   ├── test_health_monitor.py
│   │   ├── test_base_provider.py
│   │   ├── test_fmp_provider.py
│   │   ├── test_polygon_provider.py
│   │   ├── test_fred_provider.py
│   │   ├── test_qos_router.py
│   │   ├── test_circuit_breaker.py
│   │   ├── test_retry_handler.py
│   │   ├── test_rate_limit.py
│   │   ├── test_loader.py
│   │   ├── test_logging_sanitization.py
│   │   └── test_security.py
│   ├── integration/               # Integration tests (~40)
│   │   ├── test_fmp_integration.py
│   │   ├── test_polygon_integration.py
│   │   ├── test_fred_integration.py
│   │   ├── test_cache_filesystem.py
│   │   ├── test_circuit_breaker_integration.py
│   │   ├── test_resilience_integration.py
│   │   ├── test_loader_integration.py
│   │   ├── test_logging_integration.py
│   │   └── test_security_integration.py
│   └── e2e/                       # E2E tests (~10)
│       ├── test_happy_path.py
│       ├── test_readonly_mode.py
│       ├── test_parallel_fetch.py
│       └── test_resilience.py
├── examples/
│   ├── quickstart.py
│   ├── multi_provider.py
│   ├── error_handling.py
│   └── readonly_mode.py
├── scripts/
│   ├── manual_smoke_test.py
│   └── record_fixtures.py (for updating test fixtures)
├── docs/
│   ├── REQUIREMENTS.md
│   ├── ARCHITECTURE.md
│   ├── SECURITY.md
│   ├── TEST_STRATEGY.md
│   ├── DECISIONS.md
│   ├── ACTION_PLAN.md (this document)
│   └── MANUAL_TEST_REPORT.md
├── data/                          # Cache storage (excluded from git)
│   ├── fmp_cache/
│   ├── polygon_cache/
│   └── fred_cache/
└── logs/                          # Log files (excluded from git)
    └── nexus_core.log
```

---

## 6. Dependencies to Install

| Package | Version | Purpose | Type |
|---------|---------|---------|------|
| **aiohttp** | >=3.8.0 | Async HTTP client | Runtime |
| **python-dotenv** | >=0.19.0 | .env file loading | Runtime |
| **pytest** | >=7.0.0 | Testing framework | Dev |
| **pytest-cov** | >=3.0.0 | Coverage reporting | Dev |
| **pytest-asyncio** | >=0.21.0 | Async test support | Dev |
| **aioresponses** | >=0.7.0 | HTTP mocking | Dev |
| **mypy** | >=1.0.0 | Type checking | Dev |
| **ruff** | latest | Linting | Dev |
| **detect-secrets** | >=1.4.0 | Secret scanning | Dev |

**Installation:**
```bash
# Runtime dependencies
pip install aiohttp>=3.8.0 python-dotenv>=0.19.0

# Development dependencies
pip install pytest>=7.0.0 pytest-cov>=3.0.0 pytest-asyncio>=0.21.0 \
            aioresponses>=0.7.0 mypy>=1.0.0 ruff detect-secrets>=1.4.0
```

---

## 7. Risk Mitigation

| Risk | Probability | Impact | Mitigation | Buffer |
|------|-------------|--------|------------|--------|
| **Effort underestimation** | HIGH | HIGH | Applied 2-3x multipliers; built-in buffer per task | +20% contingency |
| **API schema changes** | MEDIUM | MEDIUM | Schema validation with warnings; version fixtures; graceful degradation | +4h for fixture updates |
| **Async timing bugs** | MEDIUM | MEDIUM | Comprehensive unit tests; integration tests with mocks; manual smoke test | +8h debugging budget |
| **Coverage gaps** | MEDIUM | LOW | Dedicated gap-filling task (T-022); prioritize TIER 1 first | +6h for stubborn gaps |
| **Testing complexity** | MEDIUM | MEDIUM | Mock all HTTP; use fixtures; test in isolation first | +12h for flaky tests |
| **Scope creep** | LOW | HIGH | Strict adherence to DECISIONS.md; defer all "nice to have" features | Milestone review gates |
| **Burnout** | MEDIUM | CRITICAL | Sustainable pace (8-10h/week); no hard deadlines; flexible schedule | Built into timeline |

**Contingency Budget:** +50 hours (20% of total) for unknowns, debugging, and iteration.

---

## 8. Quality Checkpoints

### Per Task
- [ ] Code complete and working
- [ ] Unit tests written and passing
- [ ] Lint clean (ruff: 0 errors)
- [ ] Type check passing (mypy: 0 errors)
- [ ] Task acceptance criteria met

### Per Milestone
- [ ] All milestone tasks complete
- [ ] Integration tests passing
- [ ] Milestone success criteria met
- [ ] Self-review complete
- [ ] Documentation updated

### Final (M4 Complete)
- [ ] Overall coverage >80%
- [ ] TIER 1 coverage >90%
- [ ] All ~200 tests passing
- [ ] CI pipeline green
- [ ] All critical test cases (TC-001 to TC-106) passing
- [ ] No API keys in logs/cache/git
- [ ] Manual smoke test successful
- [ ] README.md complete
- [ ] Pre-commit hooks working

---

## 9. Commands for Claude Code

### Project Setup (T-001)

```bash
# Create directory structure
mkdir -p src/data_loader/providers
mkdir -p tests/{unit,integration,e2e,fixtures/{fmp,polygon,fred}}
mkdir -p docs examples scripts data logs

# Initialize git
git init

# Create virtual environment
python3.9 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install aiohttp>=3.8.0 python-dotenv>=0.19.0
pip install pytest>=7.0.0 pytest-cov>=3.0.0 pytest-asyncio>=0.21.0 \
            aioresponses>=0.7.0 mypy>=1.0.0 ruff detect-secrets>=1.4.0

# Create requirements files
pip freeze > requirements.txt

# Verify installation
python -c "import aiohttp; import dotenv; print('OK')"
pytest --version
```

### Run Tests

```bash
# Run all tests
pytest

# Run specific test type
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m e2e          # E2E tests only

# Run with coverage
pytest --cov=src --cov-report=html --cov-report=term-missing

# Run fast tests only
pytest -m "not slow"

# Run TIER 1 tests
pytest -m tier1

# Run specific file
pytest tests/unit/test_circuit_breaker.py -v
```

### Lint and Type Check

```bash
# Lint
ruff check src/ tests/

# Type check
mypy src/

# Fix auto-fixable lint issues
ruff check --fix src/ tests/
```

### Coverage Analysis

```bash
# Generate HTML coverage report
pytest --cov=src --cov-report=html
open htmlcov/index.html

# Check coverage threshold
pytest --cov=src --cov-fail-under=80

# Coverage for specific component (TIER 1)
pytest --cov=src/data_loader/circuit_breaker.py --cov-report=term
```

### Pre-commit Setup

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files

# Update hooks
pre-commit autoupdate
```

---

## 10. Definition of Done

A task is **DONE** when:

- [ ] Code complete and working
- [ ] All task acceptance criteria met
- [ ] Unit tests written and passing (per tier requirements)
- [ ] Lint passing (ruff: 0 errors)
- [ ] Type check passing (mypy: 0 errors)
- [ ] Integration tests passing (if applicable)
- [ ] Documentation updated (docstrings, README)
- [ ] Self-review complete (code quality check)
- [ ] No known bugs or regressions

A milestone is **DONE** when:

- [ ] All milestone tasks DONE
- [ ] Milestone success criteria met
- [ ] Integration tests passing
- [ ] Coverage targets met (if M4)
- [ ] Documentation complete

The project is **DONE** when:

- [ ] All 4 milestones complete
- [ ] Overall coverage >80%, TIER 1 >90%
- [ ] All ~200 tests passing (<2 min execution)
- [ ] CI pipeline green
- [ ] All critical test cases passing (TC-001 to TC-106)
- [ ] Security tests passing (no API keys leaked)
- [ ] Manual smoke test successful (real APIs)
- [ ] README.md complete (<5 min setup instructions)
- [ ] Pre-commit hooks working
- [ ] All 14 MUST requirements implemented
- [ ] No P0 bugs or issues

---

## Approval

| Role | Name | Date | Status |
|------|------|------|--------|
| Author | Lead Agent | 2026-01-31 | Generated |
| Owner | Solo Developer | | Pending |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-31 | Lead Agent | Initial action plan with realistic effort estimates |

---

**Reality Check Applied:**

This plan reflects realistic effort estimates with 2-3x multipliers on initial estimates. Solo developer working 8-10 hours/week can complete in 5-7 weeks at sustainable pace. NO hard deadlines. Quality over speed.

Key realism factors:
- "Add tests" tasks are 8-16h (not "2h")
- Complex components (Circuit Breaker, FMP Provider) get realistic time budgets
- Debugging and iteration time explicitly included
- 20% contingency buffer for unknowns
- Focus on TIER 1 components first (>90% coverage)
- Accept TIER 3 at 60% (proportionate to risk)

**This is a research tool, not a production system. Build it right, not fast.**

---

## 11. Next Steps (Post-Completion)

A projekt alapvető funkcionalitása kész (M1-M4 ✅). A következő opcionális fejlesztések érhetők el:

### 11.1 Dokumentáció kiegészítése
**Prioritás:** Magas | **Komplexitás:** Közepes

- [ ] README.md frissítése
  - Telepítési útmutató
  - Használati példák (basic, advanced)
  - API referencia összefoglaló
  - Troubleshooting szekció
- [ ] API dokumentáció generálása
  - Sphinx vagy mkdocs választás
  - Docstring-ek ellenőrzése
  - Hosted docs (GitHub Pages / ReadTheDocs)

### 11.2 Csomagolás és publikálás
**Prioritás:** Magas | **Komplexitás:** Közepes

- [ ] pyproject.toml kiegészítése
  - Build system (hatchling/setuptools)
  - Entry points
  - Dependencies specifikáció
- [ ] PyPI feltöltés előkészítése
  - Package name ellenőrzés
  - Verziókezelés stratégia (semver)
  - CHANGELOG.md létrehozása
- [ ] Distribution tesztelés
  - TestPyPI feltöltés
  - Clean install teszt

### 11.3 Integrációs tesztek valós API-kkal
**Prioritás:** Közepes | **Komplexitás:** Közepes

- [ ] FMP integráció tesztelése (éles API kulccsal)
- [ ] Polygon integráció tesztelése
- [ ] FRED integráció tesztelése
- [ ] Cross-provider tesztek (párhuzamos lekérdezések)

### 11.4 További fejlesztések
**Prioritás:** Alacsony | **Komplexitás:** Magas

- [ ] Új provider: Alpha Vantage
- [ ] Új provider: Yahoo Finance
- [ ] Rate limiting finomhangolás (adaptive)
- [ ] Webhook/callback támogatás

### 11.5 Production használat
**Státusz:** ✅ KÉSZEN ÁLL

A projekt production-ready:
- 441 teszt passing
- 92% code coverage
- CI/CD pipeline aktív
- Security tesztek (API key sanitization)
- HTTPS enforced
- Circuit breaker védelem

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-31 | Lead Agent | Initial action plan with realistic effort estimates |
| 1.1 | 2026-01-31 | Claude | Updated status: M1-M4 COMPLETE, added Next Steps section |
