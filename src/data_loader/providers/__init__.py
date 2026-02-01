"""
OmniData Nexus Core - Data Providers Package

This package contains provider implementations for each data source:
    - FMPProvider: Financial Modeling Prep (189 endpoints)
    - PolygonProvider: Polygon.io (4 endpoints)
    - FREDProvider: Federal Reserve Economic Data (32 series)

All providers inherit from BaseDataProvider and implement:
    - fetch(): Async data fetching
    - normalize(): Response normalization
    - cache_key(): Cache key generation
"""

# Exports
from .base import BaseDataProvider, ProviderResponse

# FMP provider from new modular package
from .fmp import FMPProvider, create_fmp_provider, get_registry as get_fmp_registry

from .fred import FREDProvider, create_fred_provider
from .polygon import PolygonProvider, create_polygon_provider

__all__ = [
    "BaseDataProvider",
    "ProviderResponse",
    "FMPProvider",
    "create_fmp_provider",
    "get_fmp_registry",
    "PolygonProvider",
    "create_polygon_provider",
    "FREDProvider",
    "create_fred_provider",
]
