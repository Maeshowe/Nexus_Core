"""
OmniData Nexus Core - Test Configuration

Shared pytest fixtures and configuration for all test types.
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import MagicMock

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# =============================================================================
# Test Markers
# =============================================================================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests (fast, isolated)")
    config.addinivalue_line("markers", "integration: Integration tests (may use real APIs)")
    config.addinivalue_line("markers", "e2e: End-to-end tests (full workflow)")
    config.addinivalue_line("markers", "slow: Tests that take longer to run")
    config.addinivalue_line("markers", "fmp: Tests for FMP provider")
    config.addinivalue_line("markers", "polygon: Tests for Polygon provider")
    config.addinivalue_line("markers", "fred: Tests for FRED provider")


# =============================================================================
# Environment Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def test_env() -> Generator[dict, None, None]:
    """Provide test environment variables."""
    env = {
        "FMP_KEY": "test_fmp_key_12345",
        "POLYGON_KEY": "test_polygon_key_12345",
        "FRED_KEY": "test_fred_key_12345",
        "CACHE_TTL_DAYS": "1",
        "MAX_RETRIES": "2",
        "LOG_LEVEL": "DEBUG",
    }

    # Store original values
    original = {k: os.environ.get(k) for k in env}

    # Set test values
    for k, v in env.items():
        os.environ[k] = v

    yield env

    # Restore original values
    for k, v in original.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


@pytest.fixture
def temp_cache_dir() -> Generator[Path, None, None]:
    """Provide a temporary directory for cache testing."""
    with tempfile.TemporaryDirectory(prefix="nexus_test_cache_") as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_log_dir() -> Generator[Path, None, None]:
    """Provide a temporary directory for log testing."""
    with tempfile.TemporaryDirectory(prefix="nexus_test_logs_") as tmpdir:
        yield Path(tmpdir)


# =============================================================================
# Mock Session Fixtures
# =============================================================================

@pytest.fixture
def mock_session() -> MagicMock:
    """Provide a mock aiohttp ClientSession."""
    session = MagicMock()
    session.get = MagicMock()
    session.closed = False
    return session


# =============================================================================
# Sample Data Fixtures
# =============================================================================

@pytest.fixture
def sample_fmp_profile() -> dict:
    """Sample FMP company profile response."""
    return {
        "symbol": "AAPL",
        "companyName": "Apple Inc.",
        "currency": "USD",
        "exchange": "NASDAQ",
        "industry": "Consumer Electronics",
        "sector": "Technology",
        "country": "US",
        "mktCap": 3000000000000,
        "price": 185.50,
    }


@pytest.fixture
def sample_polygon_aggs() -> dict:
    """Sample Polygon aggregates response."""
    return {
        "ticker": "SPY",
        "queryCount": 5,
        "resultsCount": 5,
        "adjusted": True,
        "results": [
            {"o": 450.0, "h": 452.0, "l": 449.0, "c": 451.5, "v": 1000000, "t": 1704067200000},
            {"o": 451.5, "h": 453.0, "l": 450.5, "c": 452.0, "v": 1100000, "t": 1704153600000},
        ],
    }


@pytest.fixture
def sample_fred_series() -> dict:
    """Sample FRED series response."""
    return {
        "realtime_start": "2024-01-01",
        "realtime_end": "2024-01-31",
        "observation_start": "2024-01-01",
        "observation_end": "2024-01-31",
        "units": "lin",
        "output_type": 1,
        "file_type": "json",
        "order_by": "observation_date",
        "sort_order": "asc",
        "count": 1,
        "offset": 0,
        "limit": 100000,
        "observations": [
            {"realtime_start": "2024-01-01", "realtime_end": "2024-01-31", "date": "2024-01-01", "value": "308.417"},
        ],
    }


# =============================================================================
# Async Fixtures
# =============================================================================

@pytest.fixture
def event_loop_policy():
    """Return the default event loop policy."""
    import asyncio
    return asyncio.DefaultEventLoopPolicy()
