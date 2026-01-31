"""
OmniData Nexus Core - Data Providers Package

This package contains provider implementations for each data source:
    - FMPProvider: Financial Modeling Prep (13 endpoints)
    - PolygonProvider: Polygon.io (4 endpoints)
    - FREDProvider: Federal Reserve Economic Data (32 series)

All providers inherit from BaseDataProvider and implement:
    - fetch(): Async data fetching
    - normalize(): Response normalization
    - cache_key(): Cache key generation
"""

# Exports
from .base import BaseDataProvider, ProviderResponse
from .fmp import FMPProvider, create_fmp_provider
from .polygon import PolygonProvider, create_polygon_provider
from .fred import FREDProvider, create_fred_provider

__all__ = [
    "BaseDataProvider",
    "ProviderResponse",
    "FMPProvider",
    "create_fmp_provider",
    "PolygonProvider",
    "create_polygon_provider",
    "FREDProvider",
    "create_fred_provider",
]
