# Changelog

All notable changes to OmniData Nexus Core will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
