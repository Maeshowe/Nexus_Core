# Test Strategy

> **Project:** OmniData Nexus Core
> **Version:** 1.0
> **Date:** 2026-01-31
> **Status:** Draft
> **Phase:** DEVELOPMENT (not yet live)

---

## 1. Overview

### 1.1 Scope

**In Scope:**
- Unit tests for all core components (DataLoader, QoS Router, Circuit Breaker, Providers, Cache Manager)
- Integration tests for provider API interactions (mocked)
- End-to-end tests for critical user workflows
- Security tests for API key sanitization and HTTPS enforcement
- Resilience tests for circuit breaker, retry logic, and rate limiting

**Out of Scope:**
- Real API calls in CI/CD (all external API interactions will be mocked)
- Performance/load testing beyond basic concurrency validation (personal tool, not production service)
- UI testing (no graphical interface)
- Multi-user/concurrent process testing (single-user system)
- Network security penetration testing (local-only deployment)

### 1.2 Quality Objectives

| Objective | Target | Measurement |
|-----------|--------|-------------|
| Overall line coverage | >80% | pytest-cov |
| TIER 1 coverage | >90% | pytest-cov (filtered by component) |
| TIER 2 coverage | >80% | pytest-cov (filtered by component) |
| Test pass rate | 100% | CI pipeline |
| Test suite execution time | <2 minutes | CI pipeline |
| Security test coverage | 100% critical cases | Manual verification |

---

## 2. Test Pyramid

```
                    ┌─────────┐
                   ╱   E2E    ╲        ← 5%: Critical user workflows
                  ╱   (~10)    ╲          (cache miss→API→cache write)
                 ╱───────────────╲
                ╱   Integration   ╲    ← 20%: Provider mocking, retries
               ╱      (~40)       ╲      (aioresponses for HTTP mocking)
              ╱─────────────────────╲
             ╱        Unit           ╲  ← 75%: Isolated component logic
            ╱       (~150)            ╲    (pure functions, state machines)
           ╱───────────────────────────╲
```

**Rationale for Pyramid:**
- **Unit (75%):** Fast feedback loop; isolates bugs to specific components; enables TDD workflow
- **Integration (20%):** Validates provider-specific behavior (HTTP mocking); verifies retry/backoff logic
- **E2E (5%):** Ensures critical paths work end-to-end; validates component orchestration

**Scale-Appropriate for Solo Developer:**
- Target ~200 total tests (not thousands)
- Focus on high-risk areas (Circuit Breaker, Cache integrity, API key sanitization)
- Accept manual testing for low-risk utilities

---

## 3. Risk-Based Tiers

| Tier | Components | Coverage Target | Rationale |
|------|------------|-----------------|-----------|
| **TIER 1** | Circuit Breaker, QoS Semaphore Router, API Key Sanitization, Atomic Cache Writes | 90%+ | High risk: System resilience, security, data integrity |
| **TIER 2** | DataLoader, Providers (FMP/Polygon/FRED), Retry Handler, Health Monitor | 80% | Medium risk: Core business logic, user-facing API |
| **TIER 3** | Config Manager, Cache Manager (non-atomic methods), Logging utilities | 60% | Low risk: Wrappers, simple utilities |
| **TIER 4** | Example scripts, one-off tools | Manual testing OK | Minimal risk: Not part of core framework |

### Component Classification

| Component | Tier | Rationale | Priority Tests |
|-----------|------|-----------|----------------|
| **Circuit Breaker Manager** | 1 | Prevents cascading failures; critical resilience pattern | - State transitions (CLOSED→OPEN→HALF-OPEN)<br>- Error rate threshold (20%)<br>- Recovery logic |
| **QoS Semaphore Router** | 1 | Prevents rate limit violations; quota management | - Concurrency limits (FMP:3, Polygon:10, FRED:1)<br>- Acquire/release semantics<br>- Timeout handling |
| **API Key Sanitization** | 1 | Security: Prevents credential leakage | - Keys not in logs (regex test)<br>- Keys not in error messages<br>- Keys not in cache files |
| **Cache Atomic Writes** | 1 | Data integrity: Prevents corruption | - Concurrent writes (no partial JSON)<br>- Temp file + rename pattern<br>- Rollback on error |
| **DataLoader** | 2 | Unified interface; orchestrates all components | - Mode switching (LIVE/READ-ONLY)<br>- Provider routing<br>- Health report aggregation |
| **FMP Provider** | 2 | 13 endpoints; most complex provider | - Endpoint coverage (screener, profile, financials)<br>- Normalization logic<br>- Cache key generation |
| **Polygon Provider** | 2 | 4 endpoints; options complexity | - aggs_daily, trades, options_snapshot<br>- Hash-based cache keys<br>- Response validation |
| **FRED Provider** | 2 | 32 series; time series data | - Series fetch (CPIAUCSL, UNRATE, DGS10)<br>- Date range handling<br>- Data normalization |
| **Retry Handler** | 2 | Exponential backoff + jitter | - Retry only 5xx/timeout<br>- Max retries (3)<br>- Jitter randomization |
| **Health Monitor** | 2 | Metrics tracking | - Request/error counters<br>- Error rate calculation<br>- Per-provider stats |
| **Config Manager** | 3 | Environment variable loading | - .env file parsing<br>- Default values<br>- Validation |
| **Cache Manager (read)** | 3 | Simple file I/O | - get_cached() logic<br>- TTL expiration check<br>- Missing file handling |
| **HTTP Client Layer** | 3 | Thin wrapper over aiohttp | - Timeout configuration<br>- Connection pooling<br>- TLS enforcement |

---

## 4. Test Types

### 4.1 Unit Tests

| Target | Framework | Mocking Approach | Example |
|--------|-----------|------------------|---------|
| Circuit Breaker state machine | pytest | Mock time.time() for threshold testing | `test_circuit_breaker_opens_at_20_percent_error_rate()` |
| QoS Semaphore limits | pytest-asyncio | No mocking (test semaphore directly) | `test_qos_router_enforces_fmp_limit_3()` |
| Provider normalization | pytest | Mock HTTP responses (aioresponses) | `test_fmp_profile_normalizes_response()` |
| Cache key generation | pytest | No mocking (pure function) | `test_cache_key_md5_hash_consistency()` |
| Retry backoff calculation | pytest | Mock random.uniform() for jitter | `test_exponential_backoff_with_jitter()` |

**Isolation Strategy:**
- Mock external dependencies (`aiohttp.ClientSession`, filesystem, time)
- Use dependency injection where possible (pass session as parameter)
- Test pure functions first (cache_key generation, normalization logic)

### 4.2 Integration Tests

| Integration Point | Approach | Environment | Example |
|-------------------|----------|-------------|---------|
| **FMP API (mocked)** | aioresponses library | Mock HTTP server | `test_fmp_provider_handles_429_rate_limit()` |
| **Polygon API (mocked)** | aioresponses library | Mock HTTP server | `test_polygon_retry_on_503_server_error()` |
| **FRED API (mocked)** | aioresponses library | Mock HTTP server | `test_fred_circuit_breaker_opens_after_failures()` |
| **Filesystem cache** | tempfile.TemporaryDirectory | Isolated temp dir | `test_cache_atomic_write_concurrent_safety()` |
| **Health monitor integration** | pytest-asyncio | In-memory counters | `test_health_report_aggregates_all_providers()` |

**Mocking Rationale:**
- No real API calls in CI (cost, rate limits, reliability)
- Faster test execution (<2 min target)
- Deterministic test results (no flaky tests from network issues)

### 4.3 E2E Tests

| Scenario | Priority | Automation | Components Involved | Expected Outcome |
|----------|----------|------------|---------------------|------------------|
| **Happy path: Cache miss → API → Cache hit** | HIGH | Yes | DataLoader, Provider, Cache, HTTP Client | - 1st call: API fetch + cache write<br>- 2nd call: Cache hit (no API) |
| **Circuit breaker opens after failures** | HIGH | Yes | Circuit Breaker, Provider, Health Monitor | - 3 failures → circuit OPEN<br>- Subsequent calls fail immediately |
| **READ-ONLY mode (no API calls)** | HIGH | Yes | DataLoader, Cache | - Cache hit: success<br>- Cache miss: error (no API call) |
| **QoS limits concurrent requests** | MEDIUM | Yes | QoS Router, Provider | - FMP: max 3 concurrent (10 attempted)<br>- Verify semaphore enforcement |
| **Rate limit handling (HTTP 429)** | MEDIUM | Yes | Retry Handler, Provider | - Mock 429 response<br>- Parse Retry-After header<br>- Exponential backoff |
| **Parallel multi-provider fetch** | MEDIUM | Yes | DataLoader, All Providers | - Fetch FMP + Polygon + FRED concurrently<br>- Verify total time ≈ slowest request |
| **Graceful degradation (1 provider down)** | LOW | Manual | DataLoader, Circuit Breaker | - FMP down (circuit OPEN)<br>- Polygon/FRED still work |
| **Cache TTL expiration** | LOW | Manual | Cache Manager | - Cache entry older than TTL<br>- Refetch from API |

**E2E Test Environment:**
- Mocked HTTP responses (aioresponses)
- Temporary filesystem cache
- Isolated asyncio event loop per test

---

## 5. Test Environment

| Environment | Purpose | API Behavior | Data Source | Config |
|-------------|---------|--------------|-------------|--------|
| **Local Development** | Manual testing, debugging | Mocked (aioresponses) OR real API (opt-in via .env.local) | Test fixtures | `.env.test` (mock keys) |
| **CI/CD (GitHub Actions)** | Automated testing | Mocked only (no real API calls) | Test fixtures | Environment variables (mock keys) |
| **Manual Testing** | Exploratory testing, one-off scenarios | Real API calls (user's keys) | Real API responses | `.env` (real keys) |

**Test Data Strategy:**

| Data Type | Source | Example |
|-----------|--------|---------|
| **FMP responses** | JSON fixtures in `tests/fixtures/fmp/` | `profile_AAPL.json`, `balance_sheet_MSFT.json` |
| **Polygon responses** | JSON fixtures in `tests/fixtures/polygon/` | `aggs_daily_SPY.json`, `options_snapshot_AAPL.json` |
| **FRED responses** | JSON fixtures in `tests/fixtures/fred/` | `CPIAUCSL.json`, `UNRATE.json` |
| **Error responses** | Inline JSON in tests | `{"error": "Invalid API key"}` |

**Fixture Management:**
- Record real API responses once (via manual script)
- Store as JSON files in version control
- Update fixtures when API schemas change

---

## 6. Quality Gates

### CI/CD Pipeline

```
[Commit] → [Lint] → [Type Check] → [Unit] → [Integration] → [E2E] → [Coverage] → [Security] → [Pass]
              │          │            │           │             │          │            │
              ▼          ▼            ▼           ▼             ▼          ▼            ▼
          ruff/flake8   mypy      pytest -m    pytest -m    pytest -m   pytest-cov    Secret scan
          0 errors    0 errors     unit      integration     e2e       >80% overall     0 leaks
                                 100% pass    100% pass     100% pass   >90% TIER 1
```

### Gate Definitions

| Gate | Tool | Threshold | Blocking? | Rationale |
|------|------|-----------|-----------|-----------|
| **Code Style (Lint)** | ruff / flake8 | 0 errors | YES | Enforces consistency; prevents common bugs |
| **Type Checking** | mypy | 0 type errors | YES | Catches type mismatches before runtime |
| **Unit Tests** | pytest -m unit | 100% pass | YES | Core logic validation; fast feedback |
| **Integration Tests** | pytest -m integration | 100% pass | YES | Provider interactions; resilience patterns |
| **E2E Tests** | pytest -m e2e | 100% pass | YES | Critical user workflows |
| **Overall Coverage** | pytest-cov | ≥80% | YES | Per NFR-006 requirement |
| **TIER 1 Coverage** | pytest-cov (filtered) | ≥90% | YES | High-risk components |
| **TIER 2 Coverage** | pytest-cov (filtered) | ≥80% | NO (warning) | Aspirational, not blocking |
| **Secret Scanning** | git grep / detect-secrets | 0 API keys found | YES | Security: Prevent credential leakage |

**Coverage Exclusions:**
- `__init__.py` files (no logic)
- Debug/print statements (tagged with `# pragma: no cover`)
- Defensive error handling for impossible states
- Deprecated code (marked for removal)

---

## 7. Automation Scope

| Test Category | Automate? | Rationale | CI Execution Time |
|---------------|-----------|-----------|-------------------|
| **Unit tests** | YES | Fast (<30s), deterministic, high value | ~20s |
| **Integration tests (mocked)** | YES | Medium speed (~1min), validates resilience | ~60s |
| **E2E tests (critical paths)** | YES | Slower (~30s), but essential workflows | ~30s |
| **E2E edge cases** | PARTIAL | Diminishing returns; manual exploratory testing | N/A |
| **Security tests (key sanitization)** | YES | Critical security validation | ~5s |
| **Dependency audit** | YES | Weekly scheduled run (not per commit) | ~10s |
| **Real API smoke tests** | NO | Cost, rate limits; manual validation on release | N/A |
| **Performance benchmarks** | NO | Personal tool; manual ad-hoc benchmarking | N/A |
| **Exploratory testing** | NO | Human judgment for edge cases | N/A |

**Total CI Time Budget:** <2 minutes (enables fast iteration)

---

## 8. Critical Test Cases

### 8.1 Resilience Tests (TIER 1)

| ID | Scenario | Type | Priority | Acceptance Criteria |
|----|----------|------|----------|---------------------|
| **TC-001** | Circuit breaker opens at >20% error rate | Unit | MUST | - Track 10 requests, 3 errors (30%)<br>- Circuit state = OPEN<br>- Subsequent calls raise CircuitOpenError |
| **TC-002** | Circuit breaker recovery (HALF-OPEN → CLOSED) | Integration | MUST | - Circuit OPEN → wait timeout → HALF-OPEN<br>- Single test request succeeds → CLOSED<br>- Normal operation resumes |
| **TC-003** | Circuit breaker stays OPEN on recovery failure | Integration | MUST | - Circuit HALF-OPEN → test request fails → OPEN<br>- Reset timeout counter |
| **TC-004** | QoS router enforces FMP concurrency (max 3) | Unit | MUST | - Launch 10 concurrent FMP requests<br>- Only 3 execute simultaneously<br>- 7 wait in queue |
| **TC-005** | QoS router enforces Polygon concurrency (max 10) | Unit | MUST | - Launch 20 concurrent Polygon requests<br>- Only 10 execute simultaneously |
| **TC-006** | QoS router enforces FRED concurrency (max 1) | Unit | MUST | - Launch 5 concurrent FRED requests<br>- Serialized execution (1 at a time) |
| **TC-007** | Exponential backoff with jitter | Unit | MUST | - 1st retry: ~1s ± jitter<br>- 2nd retry: ~2s ± jitter<br>- 3rd retry: ~4s ± jitter<br>- Max 3 retries |
| **TC-008** | Retry only on 5xx/timeout (not 4xx) | Integration | MUST | - 400 Bad Request: no retry<br>- 429 Rate Limit: cooldown (not retry)<br>- 503 Service Unavailable: retry up to 3x |

### 8.2 Security Tests (TIER 1)

| ID | Scenario | Type | Priority | Acceptance Criteria |
|----|----------|------|----------|---------------------|
| **TC-101** | API keys not logged in error messages | Unit | MUST | - Trigger error with `FMP_KEY` in URL<br>- Log output contains `***REDACTED***`<br>- Regex match fails for actual key |
| **TC-102** | API keys not logged in success messages | Unit | MUST | - Successful API call<br>- Log output contains endpoint/symbol<br>- No API key in log |
| **TC-103** | API keys not in cache files | Integration | MUST | - Fetch data with API key in URL<br>- Inspect cached JSON file<br>- Verify no key present |
| **TC-104** | .env file in .gitignore | Unit | MUST | - Parse .gitignore file<br>- Assert `.env` entry exists |
| **TC-105** | HTTPS enforcement (reject HTTP) | Unit | MUST | - Attempt HTTP URL: `http://api.example.com`<br>- Raises ValueError |
| **TC-106** | TLS certificate validation enabled | Integration | SHOULD | - Mock invalid certificate<br>- Verify aiohttp raises SSLError |

### 8.3 Cache Integrity Tests (TIER 1)

| ID | Scenario | Type | Priority | Acceptance Criteria |
|----|----------|------|----------|---------------------|
| **TC-201** | Atomic write (temp + rename pattern) | Unit | MUST | - Call cache.set()<br>- Verify temp file created first<br>- Verify rename to final path<br>- No partial file remains |
| **TC-202** | Concurrent writes (no corruption) | Integration | MUST | - 10 threads write to same cache key<br>- All writes succeed<br>- Final file is valid JSON (not partial) |
| **TC-203** | Rollback on write error | Unit | MUST | - Mock filesystem error during write<br>- Verify temp file deleted<br>- Original cache (if any) unchanged |
| **TC-204** | Cache miss returns None | Unit | MUST | - Request non-existent cache key<br>- Returns None (not error) |
| **TC-205** | Cache TTL expiration | Integration | SHOULD | - Cache entry older than TTL<br>- get_cached() returns None<br>- Triggers API refetch |

### 8.4 Provider Tests (TIER 2)

| ID | Scenario | Type | Priority | Acceptance Criteria |
|----|----------|------|----------|---------------------|
| **TC-301** | FMP profile endpoint normalization | Unit | MUST | - Mock FMP profile response<br>- Verify normalized fields (symbol, companyName, sector)<br>- Handle missing fields gracefully |
| **TC-302** | Polygon aggs_daily date range | Integration | MUST | - Request SPY data for 2024-01-01 to 2024-12-31<br>- Verify all days present<br>- Handle weekends/holidays |
| **TC-303** | FRED series fetch (CPIAUCSL) | Integration | MUST | - Request CPIAUCSL time series<br>- Verify dates + values<br>- Handle FRED-specific date format |
| **TC-304** | FMP handles HTTP 429 rate limit | Integration | SHOULD | - Mock 429 response with Retry-After: 60<br>- Verify 60s cooldown<br>- Retry after cooldown |

### 8.5 End-to-End Tests (TIER 2)

| ID | Scenario | Type | Priority | Acceptance Criteria |
|----|----------|------|----------|---------------------|
| **TC-401** | Happy path: Cache miss → API → Cache hit | E2E | MUST | - 1st call: Cache miss → API fetch → Cache write<br>- 2nd call: Cache hit (no API call)<br>- Verify same data returned |
| **TC-402** | READ-ONLY mode (no API calls) | E2E | MUST | - Set mode = READ_ONLY<br>- Cache hit: returns data<br>- Cache miss: raises ReadOnlyError (no API call) |
| **TC-403** | Parallel multi-provider fetch | E2E | SHOULD | - Fetch FMP profile + Polygon aggs + FRED CPIAUCSL<br>- All 3 return data<br>- Total time ≈ slowest single request |
| **TC-404** | Health report aggregation | E2E | SHOULD | - Execute 10 FMP calls (8 success, 2 fail)<br>- get_api_health_report()<br>- Verify: total=10, errors=2, error_rate=0.2, circuit=CLOSED |

---

## 9. Tools

| Purpose | Tool | Version | Notes |
|---------|------|---------|-------|
| **Test Framework** | pytest | ≥7.0 | Industry standard; excellent async support |
| **Async Testing** | pytest-asyncio | ≥0.21 | Enables `@pytest.mark.asyncio` decorator |
| **Coverage Reporting** | pytest-cov | ≥3.0 | Integrated with pytest; generates HTML reports |
| **HTTP Mocking** | aioresponses | ≥0.7 | Mocks `aiohttp.ClientSession` responses |
| **Temporary Files** | tempfile (built-in) | - | Isolated cache directories for tests |
| **Fixtures** | pytest fixtures | - | Reusable test setup (sessions, mock data) |
| **Parametrization** | pytest.mark.parametrize | - | Test multiple inputs efficiently |
| **Secret Scanning** | detect-secrets | ≥1.4 | Pre-commit hook for API key detection |
| **Type Checking** | mypy | ≥1.0 | Static type analysis |
| **Linting** | ruff / flake8 | Latest | Fast Python linter |
| **CI/CD** | GitHub Actions | - | Automated test execution on push |

### Test Execution Commands

```bash
# Run all tests
pytest

# Run unit tests only
pytest -m unit

# Run integration tests only
pytest -m integration

# Run E2E tests only
pytest -m e2e

# Run with coverage report
pytest --cov=src --cov-report=html --cov-report=term-missing

# Run TIER 1 tests (critical components)
pytest -m tier1

# Run fast tests only (exclude slow integration)
pytest -m "not slow"

# Run specific test file
pytest tests/test_circuit_breaker.py

# Run with verbose output
pytest -v

# Run with detailed failure output
pytest -vv

# Parallel execution (optional, for speed)
pytest -n auto  # Requires pytest-xdist
```

### Coverage Reporting

```bash
# Generate HTML coverage report
pytest --cov=src --cov-report=html
open htmlcov/index.html

# Terminal coverage summary
pytest --cov=src --cov-report=term-missing

# Coverage by component (TIER 1)
pytest --cov=src/data_loader/circuit_breaker.py --cov-report=term

# Fail if coverage below threshold
pytest --cov=src --cov-fail-under=80
```

---

## 10. Test Pyramid Breakdown

### Unit Tests (~150 tests, ~20s execution)

| Component | Test Count | Key Scenarios |
|-----------|------------|---------------|
| Circuit Breaker | 15 | State transitions, threshold calculations, timeout reset |
| QoS Semaphore Router | 12 | Concurrency limits per provider, acquire/release, timeout |
| Retry Handler | 10 | Exponential backoff, jitter, max retries, 5xx only |
| Cache Manager | 20 | Atomic writes, TTL expiration, cache key generation, file I/O |
| Config Manager | 8 | .env parsing, defaults, validation, missing keys |
| FMP Provider (normalization) | 25 | All 13 endpoints, field mapping, missing data handling |
| Polygon Provider | 15 | 4 endpoints, hash-based cache keys, date ranges |
| FRED Provider | 20 | 32 series (sample), time series parsing, date formats |
| Health Monitor | 10 | Counter increments, error rate calculation, reset |
| API Key Sanitization | 10 | Regex redaction, log output, error messages |
| DataLoader (routing) | 5 | Provider selection, mode switching, health aggregation |

### Integration Tests (~40 tests, ~60s execution)

| Integration Point | Test Count | Key Scenarios |
|-------------------|------------|---------------|
| FMP API (mocked) | 10 | 429 handling, 5xx retry, circuit breaker, cache integration |
| Polygon API (mocked) | 8 | Timeout retry, malformed JSON, cache integration |
| FRED API (mocked) | 8 | Series fetch, date range, circuit breaker |
| Cache + Filesystem | 8 | Concurrent writes, temp file cleanup, permissions |
| Circuit Breaker + Provider | 6 | Error accumulation, recovery, state persistence |

### E2E Tests (~10 tests, ~30s execution)

| Workflow | Test Count | Key Scenarios |
|----------|------------|---------------|
| Cache miss → API → Cache hit | 3 | FMP, Polygon, FRED happy paths |
| READ-ONLY mode | 2 | Cache hit success, cache miss error |
| Multi-provider parallel | 2 | All providers succeed, partial failure |
| Circuit breaker full cycle | 2 | Open → Half-Open → Closed |
| QoS limits enforcement | 1 | Concurrent request throttling |

---

## 11. What This Test Strategy Doesn't Cover (And Why That's OK)

### Excluded from Testing (Proportionate to Solo Developer Tool)

| Test Type | Why Excluded | Alternative |
|-----------|--------------|-------------|
| **Real API integration tests** | Cost, rate limits, reliability | Mock all API calls; manual smoke test on release |
| **Load/stress testing** | Personal tool, not production service | Manual ad-hoc benchmarking if needed |
| **UI/UX testing** | No graphical interface | N/A |
| **Multi-user concurrency** | Single-user system | Document limitation |
| **Security penetration testing** | No external attack surface | Pre-commit secret scanning + manual review |
| **Database testing** | No database (filesystem cache) | N/A |
| **Cross-platform testing** | macOS/Linux only (POSIX assumed) | Document Windows compatibility as out of scope |
| **Internationalization** | English only | N/A |
| **Accessibility** | No UI | N/A |

---

## 12. Test Organization

### Directory Structure

```
tests/
├── conftest.py                 # Shared fixtures (mock sessions, temp cache dirs)
├── fixtures/                   # Mock API responses
│   ├── fmp/
│   │   ├── profile_AAPL.json
│   │   ├── balance_sheet_MSFT.json
│   │   └── ...
│   ├── polygon/
│   │   ├── aggs_daily_SPY.json
│   │   └── options_snapshot_AAPL.json
│   └── fred/
│       ├── CPIAUCSL.json
│       ├── UNRATE.json
│       └── ...
├── unit/                       # Unit tests (75%)
│   ├── test_circuit_breaker.py
│   ├── test_qos_router.py
│   ├── test_retry_handler.py
│   ├── test_cache_manager.py
│   ├── test_config_manager.py
│   ├── test_fmp_provider.py
│   ├── test_polygon_provider.py
│   ├── test_fred_provider.py
│   ├── test_health_monitor.py
│   └── test_sanitization.py
├── integration/                # Integration tests (20%)
│   ├── test_fmp_integration.py
│   ├── test_polygon_integration.py
│   ├── test_fred_integration.py
│   ├── test_cache_filesystem.py
│   └── test_circuit_breaker_integration.py
└── e2e/                        # End-to-end tests (5%)
    ├── test_happy_path.py
    ├── test_readonly_mode.py
    ├── test_parallel_fetch.py
    └── test_resilience.py
```

### Pytest Markers

```python
# In conftest.py
def pytest_configure(config):
    config.addinivalue_line("markers", "unit: Unit tests (fast, isolated)")
    config.addinivalue_line("markers", "integration: Integration tests (mocked HTTP)")
    config.addinivalue_line("markers", "e2e: End-to-end tests (full workflows)")
    config.addinivalue_line("markers", "tier1: TIER 1 components (>90% coverage required)")
    config.addinivalue_line("markers", "tier2: TIER 2 components (>80% coverage required)")
    config.addinivalue_line("markers", "slow: Slow tests (>1s execution)")
    config.addinivalue_line("markers", "security: Security-critical tests")
```

---

## 13. Test Maintenance Strategy

### When to Update Tests

| Trigger | Test Update Required | Example |
|---------|---------------------|---------|
| **API schema change** | Update fixtures + normalization tests | FMP adds new field to profile response |
| **New endpoint added** | Add provider tests | FRED adds new series |
| **Requirement change** | Update acceptance criteria | Circuit breaker threshold changes to 30% |
| **Bug fix** | Add regression test | Cache corruption bug → add test for that scenario |
| **Refactoring** | Update mocks/fixtures if interfaces change | Provider base class signature changes |

### Test Fixture Refresh

```bash
# Manual script to record real API responses (run locally, not in CI)
python scripts/record_fixtures.py --provider fmp --endpoint profile --symbol AAPL
python scripts/record_fixtures.py --provider polygon --endpoint aggs_daily --symbol SPY
python scripts/record_fixtures.py --provider fred --series CPIAUCSL

# Stores responses in tests/fixtures/{provider}/
# Commit updated fixtures to version control
```

---

## 14. Success Metrics

| Metric | Target | Current | Status | Measurement |
|--------|--------|---------|--------|-------------|
| Overall line coverage | >80% | TBD | ☐ | pytest-cov |
| TIER 1 coverage | >90% | TBD | ☐ | pytest-cov (filtered) |
| Test pass rate | 100% | TBD | ☐ | CI pipeline |
| Test execution time | <2 min | TBD | ☐ | CI pipeline |
| Security test coverage | 100% critical | TBD | ☐ | Manual checklist |
| Flaky test rate | <5% | TBD | ☐ | CI re-runs |
| Bug escape rate | <10% | TBD | ☐ | Post-release issues |

**Definition of "Done" for Testing:**
- [ ] All TIER 1 components have >90% coverage
- [ ] All critical test cases (TC-001 through TC-105) passing
- [ ] No API keys detected in logs/cache (TC-101 through TC-106)
- [ ] CI pipeline green on main branch
- [ ] Test execution time <2 minutes
- [ ] All E2E workflows validated

---

## Approval

| Role | Name | Date | Status |
|------|------|------|--------|
| Author | QA Agent | 2026-01-31 | ✅ Generated |
| Technical Review | Architect Agent | | ☐ Pending |
| Owner | Solo Developer | | ☐ Pending |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-31 | QA Agent | Initial test strategy for OmniData Nexus Core |

---

**Testing Philosophy:** Scale-appropriate for a solo developer research tool. Focus on high-risk components (Circuit Breaker, QoS, Security) while accepting manual testing for low-risk utilities. All external APIs mocked in CI to ensure fast, reliable, cost-effective testing.

---

*Test strategy aligned with NFR-006 (>80% coverage) and designed for fast iteration (<2 min CI time).*
