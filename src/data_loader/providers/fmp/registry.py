"""
FMP Endpoint Registry

Central registry for all FMP API endpoints with metadata.
Enables discovery, validation, and documentation of available endpoints.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional


class Tier(Enum):
    """API tier for endpoint access."""

    FREE = "free"
    PREMIUM = "premium"


class Category(Enum):
    """FMP API endpoint categories."""

    SEARCH = "search"
    COMPANY = "company"
    QUOTES = "quotes"
    FINANCIALS = "financials"
    CHARTS = "charts"
    ECONOMICS = "economics"
    CALENDARS = "calendars"
    TRANSCRIPTS = "transcripts"
    NEWS = "news"
    INSTITUTIONAL = "institutional"
    ANALYST = "analyst"
    PERFORMANCE = "performance"
    TECHNICAL = "technical"
    ETF = "etf"
    SEC = "sec"
    INSIDER = "insider"
    INDEXES = "indexes"
    FOREX = "forex"
    CRYPTO = "crypto"
    COMMODITIES = "commodities"
    CONGRESS = "congress"
    ESG = "esg"
    DCF = "dcf"
    OTHER = "other"


@dataclass
class EndpointConfig:
    """Configuration for a single FMP endpoint."""

    name: str
    path: str
    category: Category
    tier: Tier = Tier.FREE
    description: str = ""
    required_params: list[str] = field(default_factory=list)
    optional_params: list[str] = field(default_factory=list)
    example_params: dict = field(default_factory=dict)
    normalizer: Optional[Callable] = None
    deprecated: bool = False

    @property
    def all_params(self) -> list[str]:
        """Get all parameters (required + optional)."""
        return self.required_params + self.optional_params


class EndpointRegistry:
    """
    Registry of all FMP API endpoints.

    Provides:
    - Endpoint discovery
    - Validation
    - Metadata access
    - Category-based filtering

    Usage:
        registry = EndpointRegistry()
        registry.register(EndpointConfig(...))

        # Get endpoint config
        config = registry.get("profile")

        # List endpoints by category
        company_endpoints = registry.by_category(Category.COMPANY)

        # List all free endpoints
        free_endpoints = registry.by_tier(Tier.FREE)
    """

    def __init__(self):
        self._endpoints: dict[str, EndpointConfig] = {}

    def register(self, config: EndpointConfig) -> None:
        """
        Register an endpoint.

        Args:
            config: Endpoint configuration
        """
        self._endpoints[config.name] = config

    def get(self, name: str) -> Optional[EndpointConfig]:
        """
        Get endpoint configuration by name.

        Args:
            name: Endpoint name

        Returns:
            EndpointConfig or None if not found
        """
        return self._endpoints.get(name)

    def exists(self, name: str) -> bool:
        """Check if endpoint exists."""
        return name in self._endpoints

    def all(self) -> list[EndpointConfig]:
        """Get all registered endpoints."""
        return list(self._endpoints.values())

    def names(self) -> list[str]:
        """Get all endpoint names."""
        return list(self._endpoints.keys())

    def by_category(self, category: Category) -> list[EndpointConfig]:
        """
        Get endpoints by category.

        Args:
            category: Category to filter by

        Returns:
            List of endpoint configs in category
        """
        return [ep for ep in self._endpoints.values() if ep.category == category]

    def by_tier(self, tier: Tier) -> list[EndpointConfig]:
        """
        Get endpoints by tier.

        Args:
            tier: Tier to filter by

        Returns:
            List of endpoint configs in tier
        """
        return [ep for ep in self._endpoints.values() if ep.tier == tier]

    def categories(self) -> dict[Category, int]:
        """
        Get category summary with endpoint counts.

        Returns:
            Dict of category -> endpoint count
        """
        result: dict[Category, int] = {}
        for ep in self._endpoints.values():
            result[ep.category] = result.get(ep.category, 0) + 1
        return result

    def stats(self) -> dict:
        """
        Get registry statistics.

        Returns:
            Dict with total, free, premium counts and category breakdown
        """
        all_eps = list(self._endpoints.values())
        return {
            "total": len(all_eps),
            "free": len([e for e in all_eps if e.tier == Tier.FREE]),
            "premium": len([e for e in all_eps if e.tier == Tier.PREMIUM]),
            "categories": self.categories(),
        }


# Global registry instance
_registry = EndpointRegistry()


def get_registry() -> EndpointRegistry:
    """Get the global endpoint registry."""
    return _registry


def register_endpoint(config: EndpointConfig) -> EndpointConfig:
    """
    Register an endpoint in the global registry.

    Args:
        config: Endpoint configuration

    Returns:
        The registered config (for chaining)
    """
    _registry.register(config)
    return config


def endpoint(
    name: str,
    path: str,
    category: Category,
    tier: Tier = Tier.FREE,
    description: str = "",
    required_params: Optional[list[str]] = None,
    optional_params: Optional[list[str]] = None,
) -> EndpointConfig:
    """
    Helper to create and register an endpoint.

    Args:
        name: Endpoint identifier
        path: API path (relative to base URL)
        category: Endpoint category
        tier: Access tier (FREE or PREMIUM)
        description: Human-readable description
        required_params: Required parameters
        optional_params: Optional parameters

    Returns:
        Registered EndpointConfig
    """
    config = EndpointConfig(
        name=name,
        path=path,
        category=category,
        tier=tier,
        description=description,
        required_params=required_params or [],
        optional_params=optional_params or [],
    )
    return register_endpoint(config)
