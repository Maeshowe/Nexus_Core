# Changelog

All notable changes to OmniData Nexus Core will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-02-01

### Added

- **[SC-002]** Performance benchmark tool (`tools/benchmarks/benchmark.py`)
  - API latency measurement per provider (FMP, Polygon, FRED)
  - Cache read performance benchmarking (~7k-26k req/sec)
  - Concurrent request throughput testing
  - Quick and full benchmark modes (`--full` flag)

- **[SC-003]** Example scripts (`examples/`)
  - `01_quickstart.py` - Basic multi-provider usage
  - `02_multi_provider_analysis.py` - Comprehensive stock analysis
  - `03_caching_demo.py` - Cache behavior demonstration
  - `04_error_handling.py` - Resilience patterns
  - `05_readonly_mode.py` - Offline analysis mode
  - `06_parallel_fetch.py` - Concurrent portfolio fetching

- **[SC-004]** GitHub Pages documentation
  - MkDocs with Material theme
  - mkdocstrings Python autodoc
  - Live at: https://maeshowe.github.io/Nexus_Core/

- **[SC-005]** Smoke test script (`scripts/smoke_test.py`)
  - Real API integration testing (FMP, Polygon, FRED)
  - Cache verification
  - Health report testing

### Changed

- **[TC-002]** Repository visibility: Private → Public
  - Enables GitHub Pages hosting
  - Open source release

### Fixed

- **[TC-003]** CI pipeline fixes
  - Ruff linter: Import sorting, f-string cleanup, style rules
  - Mypy type checker: Relaxed strict mode, added type annotations
  - Bandit security scan: Added `usedforsecurity=False` to MD5 hash
  - All checks now passing (Python 3.9-3.12)

---

## [1.1.0] - 2026-01-31

### Changed

- **[TC-001]** FMP API: Migrated from `/api/v3/` to `/stable/` endpoints
  - FMP deprecated the old API in August 2025
  - Symbol parameter changed from path param to query param
  - All 13 FMP endpoints updated
  - All unit/integration/e2e tests updated with new URL patterns
  - Impact: Medium (breaking change for existing URL mocks)

### Added

- **[SC-001]** Endpoint Health diagnostic tool (`tools/diagnostics/endpoint_health.py`)
  - Log parser for API error detection (429, 5xx)
  - Heatmap generation by provider/endpoint
  - CSV export for analysis
  - Supports FMP, Polygon, FRED providers
  - CLI and Python API usage

### Fixed

- Test isolation in `test_config.py`: Fixed `.env` file loading during tests
  - `clean_env` fixture now temporarily renames `.env` to prevent `load_dotenv()` interference
- Updated `.gitignore` to exclude `.claude/`, `data/`, `logs/` directories

## [1.0.0] - 2026-01-31

### Added

- Initial release of OmniData Nexus Core
- **Core Infrastructure**
  - Configuration manager with `.env` support
  - HTTP client with aiohttp
  - Filesystem-based JSON cache with TTL
  - Health monitoring and metrics
- **Data Providers**
  - FMP provider (13 endpoints)
  - Polygon provider (4 endpoints)
  - FRED provider (32+ series)
- **Resilience Layer**
  - Circuit breaker with configurable thresholds
  - Exponential backoff retry with jitter
  - QoS semaphore for concurrency control
  - Rate limit (429) handling
- **DataLoader**
  - Unified interface for all providers
  - LIVE and READ_ONLY operating modes
  - Automatic caching
  - Health report aggregation
- **Testing**
  - 441 tests (unit, integration, e2e)
  - 92% code coverage
  - Security tests for API key sanitization
- **CI/CD**
  - GitHub Actions workflow
  - Pre-commit hooks configured
