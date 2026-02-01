"""
OmniData Nexus Core - Data Loader Package

A modular, asynchronous DataLoader framework for financial and macroeconomic
data aggregation from FMP Ultimate, Polygon, and FRED APIs.

Basic Usage:
    from src.data_loader import DataLoader
    import aiohttp
    import asyncio

    async def main():
        loader = DataLoader()
        async with aiohttp.ClientSession() as session:
            data = await loader.get_fmp_data(session, "profile", symbol="AAPL")
            print(data)

    asyncio.run(main())

Components:
    - DataLoader: Unified interface for all data sources
    - Config: Configuration management (.env loading)
    - QoSRouter: Provider-specific concurrency limits
    - CircuitBreaker: Failure isolation and recovery
    - RetryHandler: Exponential backoff with jitter
    - CacheManager: Filesystem JSON cache with atomic writes
    - HealthMonitor: API status and metrics tracking

Providers:
    - FMPProvider: 13 fundamental data endpoints
    - PolygonProvider: 4 market data endpoints
    - FREDProvider: 32 macroeconomic series
"""

__version__ = "1.0.0"
__author__ = "OmniData Nexus Core Team"

# Exports - M1 Foundation components
from .cache import CacheEntry, CacheManager
from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitBreakerManager,
    CircuitState,
)
from .config import Config, OperatingMode, load_config
from .health import HealthMonitor, ProviderStatus
from .http_client import HttpClient, HttpError, HttpResponse

# Unified DataLoader interface
from .loader import DataLoader, DataLoaderStats, ReadOnlyError, create_data_loader
from .logging import get_logger, sanitize_message, setup_logging

# M3 Resilience components
from .qos_router import QoSSemaphoreRouter
from .retry import RetryConfig, RetryError, RetryHandler, RetryStats

__all__ = [
    "__version__",
    # Unified DataLoader
    "DataLoader",
    "DataLoaderStats",
    "ReadOnlyError",
    "create_data_loader",
    # Config
    "Config",
    "OperatingMode",
    "load_config",
    # HTTP
    "HttpClient",
    "HttpError",
    "HttpResponse",
    # Cache
    "CacheManager",
    "CacheEntry",
    # Health
    "HealthMonitor",
    "ProviderStatus",
    # Logging
    "setup_logging",
    "get_logger",
    "sanitize_message",
    # QoS Router
    "QoSSemaphoreRouter",
    # Circuit Breaker
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerError",
    "CircuitBreakerManager",
    "CircuitState",
    # Retry
    "RetryConfig",
    "RetryError",
    "RetryHandler",
    "RetryStats",
]
