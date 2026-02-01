"""
FMP (Financial Modeling Prep) Provider Package

Modular FMP API provider with 189 endpoints organized by category.

Categories:
    - search: Search & Directory (12 endpoints)
    - company: Company Information (13 endpoints)
    - quotes: Quotes (13 endpoints)
    - financials: Financial Statements (22 endpoints)
    - charts: Price Charts (10 endpoints)
    - calendars: Calendars & Events (9 endpoints)
    - analyst: Analyst Data (8 endpoints)
    - insider: Insider Trading (6 endpoints)
    - institutional: Institutional Ownership (7 endpoints)
    ... and more

Usage:
    from data_loader.providers.fmp import FMPProvider, get_registry

    # Get all registered endpoints
    registry = get_registry()
    print(f"Total endpoints: {registry.stats()['total']}")

    # Use provider
    provider = FMPProvider(config, http_client, cache, health_monitor)
    response = await provider.get(session, "profile", symbol="AAPL")
"""

# Import registry first (before category modules)
from .registry import (
    Category,
    EndpointConfig,
    EndpointRegistry,
    Tier,
    endpoint,
    get_registry,
    register_endpoint,
)

# Import category modules to register their endpoints
# Order doesn't matter - each module registers its endpoints on import
from . import analyst
from . import calendars
from . import charts
from . import company
from . import financials
from . import insider
from . import institutional
from . import quotes
from . import search

# Import base provider class
from .base import FMPBaseProvider

# Re-export the provider as FMPProvider for backward compatibility
FMPProvider = FMPBaseProvider

__all__ = [
    # Provider
    "FMPProvider",
    "FMPBaseProvider",
    # Registry
    "EndpointRegistry",
    "EndpointConfig",
    "Category",
    "Tier",
    "get_registry",
    "register_endpoint",
    "endpoint",
    # Category modules (for direct access if needed)
    "search",
    "company",
    "quotes",
    "financials",
    "charts",
    "calendars",
    "analyst",
    "insider",
    "institutional",
]


def create_fmp_provider(
    api_key: str,
    cache_dir: str | None = None,
    timeout: float = 30.0,
) -> FMPProvider:
    """
    Create an FMP provider with default configuration.

    Args:
        api_key: FMP API key
        cache_dir: Optional cache directory path
        timeout: Request timeout in seconds

    Returns:
        Configured FMPProvider instance
    """
    from pathlib import Path

    from ...cache import CacheManager
    from ...config import ProviderConfig
    from ...health import HealthMonitor
    from ...http_client import HttpClient

    config = ProviderConfig(
        api_key=api_key,
        base_url="https://financialmodelingprep.com",
        max_concurrency=3,
        timeout=timeout,
    )

    http_client = HttpClient(timeout=timeout)

    cache_path = Path(cache_dir) if cache_dir else Path.cwd() / "data" / "cache"
    cache = CacheManager(base_dir=cache_path)

    health_monitor = HealthMonitor()

    return FMPProvider(
        config=config,
        http_client=http_client,
        cache=cache,
        health_monitor=health_monitor,
    )
