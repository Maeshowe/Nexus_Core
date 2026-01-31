# Project Decisions

> **Project:** OmniData Nexus Core
> **Version:** 1.0
> **Date:** 2026-01-31
> **Status:** Draft
> **Synthesized by:** Synthesizer Agent

---

## 1. Project Identity

| Field | Value |
|-------|-------|
| **Name** | OmniData Nexus Core |
| **Description** | Modular asynchronous Python framework providing unified Data Access Layer for financial and macroeconomic data aggregation |
| **Type** | Personal Research Tool |
| **Phase** | DEVELOPMENT |
| **Based On** | MoneyFlows Data Loader v2.7.0 |

---

## 2. Team Context

| Factor | Value | Implications |
|--------|-------|--------------|
| Team Size | 1 (Solo Developer) | Prioritize simplicity over abstraction; avoid over-engineering; single failure domain acceptable |
| AI Assisted | Yes | CLAUDE.md important for context; documentation supports AI collaboration |
| Timeline | Research-driven | No hard deadlines; quality over speed |
| Sustainable Pace | Flexible | Personal tool allows adaptive scheduling; no external commitments |

**Key Implications:**
- Modular Monolith architecture (not microservices) - no operational overhead
- Scale-appropriate security (not enterprise) - `.env` + `.gitignore` sufficient
- Manual processes acceptable (dependency updates, key rotation)
- ~200 tests target (not thousands)

---

## 3. Problem & Solution

### Problem (from REQUIREMENTS.md)

Quantitative finance research requires data from multiple specialized APIs (FMP Ultimate, Polygon.io, FRED), each with different authentication, response formats, rate limits, and availability patterns. There is no unified framework that:

- Provides a single interface for heterogeneous financial data sources
- Implements production-grade resilience (circuit breaker, exponential backoff)
- Manages concurrent requests with provider-specific limits
- Caches responses intelligently with atomic writes
- Monitors API health and rate limit consumption automatically

### Solution (from ARCHITECTURE.md)

A **Modular Monolith with Plugin Architecture** that provides:

- **DataLoader** - Unified entry point with `get_fmp_data()`, `get_polygon_data()`, `get_fred_data()` methods
- **QoS Semaphore Router** - Provider-specific concurrency limits (FMP:3, Polygon:10, FRED:1)
- **Circuit Breaker Manager** - Per-provider failure isolation with 20% error threshold
- **Intelligent Cache** - Filesystem JSON with atomic writes (temp + rename pattern)
- **Health Monitor** - Request/error tracking with per-provider status

**50 Endpoints Total:** 13 FMP + 4 Polygon + 32 FRED series + 1 FRED base

---

## 4. Key Decisions

### 4.1 Technology Stack (from ARCHITECTURE.md)

| Layer | Decision | Rationale |
|-------|----------|-----------|
| Language | Python 3.9+ | Async/await improvements; widespread in quant research; asyncio stability |
| Async HTTP | aiohttp (>=3.8) | Production-ready async client; connection pooling; timeout control |
| Environment | python-dotenv (>=0.19) | Standard .env file loading; keeps secrets out of code |
| Testing | pytest (>=7.0) + pytest-cov (>=3.0) + pytest-asyncio (>=0.21) | Industry standard; excellent async support |
| HTTP Mocking | aioresponses (>=0.7) | Mocks aiohttp.ClientSession for testing |
| Type Checking | mypy (>=1.0) | Static type analysis |
| Linting | ruff / flake8 | Fast Python linter |
| Caching | Filesystem (JSON) | Simple, human-readable, no DB overhead |

**No Database Dependencies** - Filesystem cache sufficient for research workload.

### 4.2 Architecture Decisions

| ID | Decision | Source | Consequences |
|----|----------|--------|--------------|
| AD-001 | Modular Monolith over Microservices | ARCHITECTURE.md | (+) Simple deployment, fast iteration, no network overhead; (-) All components share failure domain |
| AD-002 | Filesystem JSON cache (not Redis/DB) | ARCHITECTURE.md | (+) Zero external dependencies, inspectable; (-) No TTL auto-expiration, manual cleanup needed |
| AD-003 | Provider-specific concurrency limits (QoS Semaphore) | ARCHITECTURE.md | (+) Prevents rate limit violations, maximizes throughput; (-) Requires tuning per API subscription tier |
| AD-004 | Circuit Breaker per provider (not global) | ARCHITECTURE.md | (+) Isolates failures, allows partial service; (-) More complex state management |
| AD-005 | Atomic cache writes (temp + rename) | ARCHITECTURE.md | (+) Guarantees consistency, prevents corruption; (-) Extra filesystem operation per write |
| AD-006 | Plugin architecture (BaseDataProvider) | ARCHITECTURE.md | (+) Extensibility, separation of concerns; (-) Slight abstraction overhead |
| AD-007 | Exponential backoff with jitter (not linear) | ARCHITECTURE.md | (+) Prevents thundering herd, faster recovery; (-) More complex retry logic |
| AD-008 | Operating modes (LIVE vs READ-ONLY) | ARCHITECTURE.md | (+) Explicit control, enables airplane mode; (-) Mode management adds complexity |
| AD-009 | Schema validation (warn, don't fail) | ARCHITECTURE.md | (+) Robustness to API changes; (-) May mask breaking changes |
| AD-010 | Async/await (not threading) | ARCHITECTURE.md | (+) Efficient concurrency, single-threaded simplicity; (-) All code must be async-compatible |

### 4.3 Security Decisions (from SECURITY.md)

| ID | Decision | Risk Level |
|----|----------|------------|
| SD-001 | API keys stored in `.env` file (plaintext) with chmod 600 + .gitignore | LOW (appropriate for single-user local tool) |
| SD-002 | No encryption at rest for cache (public financial data) | NEGLIGIBLE |
| SD-003 | No user authentication (single-user system) | NONE (appropriate for use case) |
| SD-004 | Manual dependency updates (not automated) | LOW (weekly pip audit schedule) |
| SD-005 | TLS 1.2+ enforced via aiohttp (HTTPS only) | N/A (standard security) |
| SD-006 | API key sanitization in logs (regex-based redaction) | N/A (required control) |
| SD-007 | Pre-commit hook for secret scanning | N/A (required control) |

**Security Philosophy:** Proportionate security for personal research tool. Focus on API key protection. NOT requiring OAuth, RBAC, SIEM, or enterprise-grade controls.

### 4.4 Quality Decisions (from TEST_STRATEGY.md)

| ID | Decision | Target |
|----|----------|--------|
| QD-001 | Overall line coverage | >80% |
| QD-002 | TIER 1 coverage (Circuit Breaker, QoS, Security, Cache Atomic) | >90% |
| QD-003 | TIER 2 coverage (DataLoader, Providers, Retry, Health) | >80% |
| QD-004 | TIER 3 coverage (Config, Cache read, HTTP wrapper) | 60% |
| QD-005 | Test pass rate | 100% |
| QD-006 | Test suite execution time | <2 minutes |
| QD-007 | Test pyramid ratio | 75% unit / 20% integration / 5% E2E |
| QD-008 | Total test target | ~200 tests |
| QD-009 | All external APIs mocked in CI | Yes (no real API calls) |

---

## 5. Scope Boundaries

### In Scope (MVP)

| ID | Feature | Source | Priority |
|----|---------|--------|----------|
| FR-001 | Unified DataLoader Interface | REQUIREMENTS.md | MUST |
| FR-002 | FMP Ultimate Integration (13 endpoints) | REQUIREMENTS.md | MUST |
| FR-003 | Polygon Integration (4 endpoints) | REQUIREMENTS.md | MUST |
| FR-004 | FRED Integration (32 series) | REQUIREMENTS.md | MUST |
| FR-005 | QoS Semaphore Router | REQUIREMENTS.md | MUST |
| FR-006 | Intelligent Caching | REQUIREMENTS.md | MUST |
| FR-007 | Circuit Breaker | REQUIREMENTS.md | MUST |
| FR-008 | Exponential Backoff with Jitter | REQUIREMENTS.md | MUST |
| FR-009 | Rate Limit Handling | REQUIREMENTS.md | MUST |
| FR-010 | Health Check System | REQUIREMENTS.md | MUST |
| FR-011 | Schema-based Validation | REQUIREMENTS.md | MUST |
| FR-012 | Operating Modes (LIVE/READ-ONLY) | REQUIREMENTS.md | MUST |
| FR-013 | Configuration Management | REQUIREMENTS.md | MUST |
| FR-014 | API Key Sanitization | REQUIREMENTS.md | MUST |
| FR-101 | Cache TTL Configuration | REQUIREMENTS.md | SHOULD |
| FR-102 | Request Batching | REQUIREMENTS.md | SHOULD |
| FR-103 | Metrics Export | REQUIREMENTS.md | SHOULD |
| FR-104 | Graceful Degradation | REQUIREMENTS.md | SHOULD |

### Explicitly Out of Scope

| Item | Reason | Revisit When |
|------|--------|--------------|
| GUI Dashboard | Focus on programmatic API | User requests UI |
| Database Persistence | Caller responsible for storage | Multi-user requirement |
| Data Analysis/Modeling | Framework provides data, not analytics | Never (separate concern) |
| Multi-user Authentication | Single-user research tool | Multi-user requirement |
| WebSocket Streaming | REST endpoints sufficient for research | Real-time requirement |
| Cross-platform (Windows) | POSIX assumed (macOS/Linux) | User requests Windows support |
| Enterprise Security (Vault, OAuth, RBAC) | Overkill for personal tool | Commercial deployment |

### Deferred (Post-MVP)

| Item | Effort | Trigger |
|------|--------|---------|
| FR-201: Plugin Discovery Registry | 8h | Adding 3+ new data sources |
| FR-202: Dark Pool Detection | 8h | Research requires block trade analysis |
| FR-203: Data Export (Parquet/HDF5) | 12h | Data persistence needs grow |
| FR-204: CLI Tool | 8h | Manual query frequency increases |
| FR-205: Async Iterator Support | 20h | Memory limits hit with large datasets |
| Prometheus Metrics Export | 12h | Operational monitoring needed |
| Database Cache Backend | 24h | Multi-process access required |

---

## 6. Known Issues & Risks

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| API schema breaking change | Medium | High | Schema validation with warnings; graceful degradation; version pinning in provider |
| Rate limit exhaustion | Medium | Medium | QoS semaphore enforces limits; 429 handling; warning at 80% consumption |
| API service outage | Medium | Medium | Circuit breaker halts requests; cache serves stale data; clear error messages |
| Cache corruption | Low | Medium | Atomic writes (temp+rename); validate JSON before write |
| Dependency vulnerability | Low | Medium | Minimal dependencies; regular pip audit; version pinning |
| Thundering herd on recovery | Low | Low | Exponential backoff with jitter; circuit breaker half-open state |
| Memory exhaustion (large datasets) | Low | High | NOT mitigated in v1.0; future: streaming/pagination; document memory limits |
| API key leakage | Low | Critical | .gitignore for .env; sanitization in logs; pre-commit hook validation |

### Known Issues (Accepted)

| Issue | Location | Why Accepted | Review Date |
|-------|----------|--------------|-------------|
| No TTL auto-expiration | Cache Manager | Filesystem cache simplicity; manual cleanup acceptable | 2026-07-31 |
| No multi-process cache access | Cache Manager | Single-user system; document limitation | When multi-process needed |
| 7-day stale data tolerance | Cache TTL | Research workload tolerates; user configurable | User feedback |
| Windows compatibility unknown | POSIX assumption | macOS/Linux primary environments | User request |

### Security Exceptions

| Exception | Reason | Risk | Approved By |
|-----------|--------|------|-------------|
| API Keys in Plaintext (.env) | Single-user local system; encrypted secret store overkill | LOW (file permissions + .gitignore) | Solo Developer |
| No Encryption at Rest (Cache) | Public financial data; no confidentiality requirement | NEGLIGIBLE | Solo Developer |
| No User Authentication | Single-user system; no network exposure | NONE | Solo Developer |
| Manual Dependency Updates | Automated updates risk breaking changes | LOW (weekly pip audit) | Solo Developer |

---

## 7. Standards

### Coding Standards

| Aspect | Standard |
|--------|----------|
| Style | ruff / flake8 (0 errors required) |
| Type Hints | mypy strict mode (0 type errors required) |
| Docstrings | Google style (Sphinx-ready) |
| Naming | snake_case (functions/variables), PascalCase (classes) |
| Comments | Required for complex logic; not for obvious code |
| Max Line Length | 120 characters (ruff default) |
| Imports | Sorted (isort compatible) |

### Git Conventions

| Aspect | Convention |
|--------|------------|
| Branch naming | `feature/FR-XXX-description`, `fix/issue-description`, `refactor/component-name` |
| Commit messages | Imperative mood: "Add circuit breaker recovery logic" (not "Added...") |
| Commit scope | Small, focused commits (one logical change per commit) |
| Main branch | `main` (protected, requires passing CI) |
| Merge strategy | Squash merge for feature branches |

### File Organization

```
src/
  data_loader/
    __init__.py
    loader.py              # DataLoader (unified interface)
    qos_router.py          # QoS Semaphore Router
    circuit_breaker.py     # Circuit Breaker Manager
    retry.py               # Retry & Backoff Handler
    cache.py               # Cache Manager
    health.py              # Health Monitor
    config.py              # Config Manager
    http_client.py         # HTTP Client Layer
    providers/
      __init__.py
      base.py              # BaseDataProvider (abstract)
      fmp.py               # FMP Provider
      polygon.py           # Polygon Provider
      fred.py              # FRED Provider
tests/
  conftest.py              # Shared fixtures
  fixtures/                # Mock API responses
  unit/                    # Unit tests (75%)
  integration/             # Integration tests (20%)
  e2e/                     # End-to-end tests (5%)
docs/
  REQUIREMENTS.md
  ARCHITECTURE.md
  SECURITY.md
  TEST_STRATEGY.md
  DECISIONS.md             # This document
data/
  fmp_cache/
  polygon_cache/
  fred_cache/
logs/
  nexus_core.log
```

---

## 8. Quality Gates

| Gate | Threshold | Blocking? | Source |
|------|-----------|-----------|--------|
| Lint (ruff/flake8) | 0 errors | YES | Standards |
| Type Check (mypy) | 0 type errors | YES | Standards |
| Unit Tests | 100% pass | YES | TEST_STRATEGY.md |
| Integration Tests | 100% pass | YES | TEST_STRATEGY.md |
| E2E Tests | 100% pass | YES | TEST_STRATEGY.md |
| Overall Coverage | >=80% | YES | TEST_STRATEGY.md (NFR-006) |
| TIER 1 Coverage | >=90% | YES | TEST_STRATEGY.md |
| TIER 2 Coverage | >=80% | NO (warning) | TEST_STRATEGY.md |
| Secret Scanning | 0 API keys found | YES | SECURITY.md |
| Test Execution Time | <2 minutes | NO (warning) | TEST_STRATEGY.md |
| Security Vulnerabilities (pip audit) | 0 HIGH/CRITICAL | YES | SECURITY.md |

**CI Pipeline Order:**
```
[Commit] -> [Lint] -> [Type Check] -> [Unit] -> [Integration] -> [E2E] -> [Coverage] -> [Secret Scan] -> [Pass]
```

---

## 9. Excluded Paths

> Agents will NOT analyze these paths during ANALYSIS phase.

| Path | Reason |
|------|--------|
| `data/` | Large cache files; not source code |
| `data/fmp_cache/` | Generated cache data |
| `data/polygon_cache/` | Generated cache data |
| `data/fred_cache/` | Generated cache data |
| `__pycache__/` | Python bytecode (generated) |
| `.git/` | Version control metadata |
| `*.pyc` | Python bytecode files |
| `.env` | Secret file (should not be analyzed) |
| `.env.*` | Environment variants |
| `venv/` | Virtual environment |
| `*.egg-info/` | Package metadata |
| `htmlcov/` | Coverage report output |
| `logs/` | Runtime logs |
| `.pytest_cache/` | Test cache |
| `.mypy_cache/` | Type checker cache |
| `tests/fixtures/` | Static test data (JSON mocks) |

---

## 10. Agent Instructions

> Special instructions for agents during ANALYSIS phase.

| Agent | Instruction |
|-------|-------------|
| **security** | Focus on API key protection (SR-001 through SR-007). This is a personal tool - do NOT flag missing enterprise controls (Vault, OAuth, RBAC) as issues. Verify .gitignore includes .env. Check for key sanitization in logging. |
| **qa** | Verify coverage targets: >80% overall, >90% TIER 1. All tests must mock external APIs (no real HTTP calls in CI). Test pyramid: 75% unit / 20% integration / 5% E2E. |
| **architect** | Validate Modular Monolith approach. Check BaseDataProvider abstraction for extensibility. Verify circuit breaker is per-provider (not global). Confirm atomic write pattern in cache. |
| **analyst** | Verify all 50 endpoints documented: 13 FMP + 4 Polygon + 32 FRED series + 1 FRED base. Check NFRs are measurable. Validate MUST/SHOULD/COULD prioritization. |
| **dx** | Check setup time target (<5 minutes). Verify installation instructions are complete. Validate .env.example exists. Check error messages are actionable. |
| **all** | Project phase is DEVELOPMENT (not LIVE). Scale-appropriate for solo developer. Avoid suggesting enterprise-grade solutions for personal tool. |

---

## 11. Trade-offs Accepted

| Trade-off | Our Choice | Rationale |
|-----------|------------|-----------|
| Simplicity vs Scalability | **Simplicity** | Solo dev, personal tool; no multi-user, no distributed deployment |
| Coverage vs Speed | **Balance** | TIER 1 = 90%, TIER 3 = 60%; risk-based prioritization |
| Automation vs Control | **Control** | Manual dependency updates to prevent breaking changes |
| Security Depth vs Overhead | **Proportionate** | .env + .gitignore, not Vault; appropriate for threat model |
| Real-time vs Batch | **Batch** | Research workload; REST sufficient, no WebSocket |
| Persistence vs Simplicity | **Simplicity** | Filesystem cache; no database overhead |
| Cross-platform vs POSIX | **POSIX** | macOS/Linux primary; Windows deferred |
| Stale Data vs Freshness | **7-day TTL** | Research tolerates stale; configurable if needed |
| Fail-fast vs Resilience | **Resilience** | Schema validation warns (not fails); partial data preferred |
| Single Process vs Multi-process | **Single** | No file locking complexity; document limitation |

---

## 12. Document References

| Document | Status | Key Sections |
|----------|--------|--------------|
| REQUIREMENTS.md | Approved | Section 4: Functional Requirements (14 MUST, 4 SHOULD); Section 5: NFRs; Appendix A: 50 Endpoints |
| ARCHITECTURE.md | Approved | Section 3: Component Architecture; Section 6: Architecture Decisions (10 ADRs); Section 9: Quality Attributes |
| SECURITY.md | Approved | Section 2: Threat Model; Section 4: Security Controls; Section 12: Risk Register (7 risks) |
| TEST_STRATEGY.md | Approved | Section 3: Risk-Based Tiers; Section 6: Quality Gates; Section 8: Critical Test Cases |

---

## 13. Concurrency Limits Reference

> Quick reference for QoS Semaphore Router configuration.

| Provider | Concurrent Requests | Rate Limit | Source |
|----------|---------------------|------------|--------|
| FMP | 3 | Plan-dependent | REQUIREMENTS.md FR-005 |
| Polygon | 10 | 5 req/min (free tier) | REQUIREMENTS.md FR-005 |
| FRED | 1 | ~120 req/min recommended | REQUIREMENTS.md FR-005 |

---

## 14. Endpoint Summary

> 50 total endpoints across 3 providers.

| Provider | Count | Endpoints |
|----------|-------|-----------|
| **FMP Ultimate** | 13 | screener, profile, quote, historical_price, earnings_calendar, balance_sheet, income_statement, cash_flow, ratios, growth, key_metrics, insider_trading, institutional_ownership |
| **Polygon** | 4 | aggs_daily, trades, options_snapshot, market_snapshot |
| **FRED** | 32 series + 1 base | CPIAUCSL, CPILFESL, PCEPI, PCEPILFE, UNRATE, PAYEMS, CES0500000003, ECIWAG, CIVPART, GDPC1, GPDI, PNFI, Y033RC1Q027SBEA, Y006RC1Q027SBEA, EXPGS, IMPGS, NETEXP, HOUST, PERMIT, HSN1F, EXHOSLUSM495S, CSUSHPINSA, DGS10, FEDFUNDS, MORTGAGE30US, AWHMAN, DGORDER, ICSA, IC4WSA, UMCSENT, UMCSENTEXP, USEPUINDXD |

---

## 15. Success Criteria

> Definition of "Done" for v1.0.

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| All MUST requirements implemented | 14/14 | Code review |
| Overall test coverage | >80% | pytest-cov |
| TIER 1 coverage | >90% | pytest-cov (filtered) |
| CI pipeline passing | Green | GitHub Actions |
| All critical test cases | Pass | TC-001 through TC-106 |
| Setup time | <5 minutes | Timed installation |
| Single API request latency | <2s p95 | Benchmark |
| No API keys in logs/cache/git | 0 found | Secret scan |
| Documentation complete | All 5 docs | Review |

---

## Approval

| Role | Name | Date | Status |
|------|------|------|--------|
| Author | Synthesizer Agent | 2026-01-31 | Generated |
| Requirements | Analyst Agent | 2026-01-31 | Approved |
| Architecture | Architect Agent | 2026-01-31 | Approved |
| Security | Security Agent | 2026-01-31 | Approved |
| Quality | QA Agent | 2026-01-31 | Approved |
| Owner | Solo Developer | | Pending |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-31 | Synthesizer Agent | Initial synthesis from REQUIREMENTS.md, ARCHITECTURE.md, SECURITY.md, TEST_STRATEGY.md |

---

*Unified project decisions synthesized from approved documentation. This document serves as the single source of truth for project scope, standards, and trade-offs.*
