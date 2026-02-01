"""
FMP Base Provider

Extended base class for FMP with registry integration.
"""

from typing import Any, Optional

import aiohttp

from ...cache import CacheManager
from ...config import ProviderConfig
from ...health import HealthMonitor
from ...http_client import HttpClient, HttpResponse
from ..base import BaseDataProvider
from .registry import EndpointConfig, EndpointRegistry, get_registry


class FMPBaseProvider(BaseDataProvider):
    """
    Base FMP provider with registry integration.

    Provides common functionality for all FMP category modules:
    - URL building with /stable/ API
    - Parameter handling
    - Endpoint validation via registry
    - Default normalization

    Subclasses implement category-specific logic if needed.
    """

    # Default base URL for FMP API
    DEFAULT_BASE_URL = "https://financialmodelingprep.com"

    def __init__(
        self,
        config: ProviderConfig,
        http_client: HttpClient,
        cache: CacheManager,
        health_monitor: HealthMonitor,
        registry: Optional[EndpointRegistry] = None,
    ):
        """
        Initialize FMP base provider.

        Args:
            config: Provider configuration
            http_client: HTTP client instance
            cache: Cache manager
            health_monitor: Health monitor
            registry: Optional custom registry (uses global if not provided)
        """
        super().__init__(config, http_client, cache, health_monitor)
        self._registry = registry or get_registry()

    @property
    def provider_name(self) -> str:
        return "fmp"

    @property
    def registry(self) -> EndpointRegistry:
        """Get the endpoint registry."""
        return self._registry

    def get_endpoint_config(self, endpoint: str) -> Optional[EndpointConfig]:
        """
        Get configuration for an endpoint.

        Args:
            endpoint: Endpoint name

        Returns:
            EndpointConfig or None
        """
        return self._registry.get(endpoint)

    def get_supported_endpoints(self) -> list[str]:
        """Get list of all supported endpoints from registry."""
        return self._registry.names()

    def validate_endpoint(self, endpoint: str) -> bool:
        """Check if endpoint exists in registry."""
        return self._registry.exists(endpoint)

    def _build_url(self, endpoint: str, **params) -> str:
        """
        Build the full URL for an endpoint.

        Args:
            endpoint: Endpoint name
            **params: Parameters (for path substitution)

        Returns:
            Full URL string

        Raises:
            ValueError: If endpoint not found
        """
        config = self.get_endpoint_config(endpoint)
        if not config:
            raise ValueError(f"Unknown endpoint: {endpoint}")

        path = config.path

        # Replace path parameters like {symbol}
        for key, value in params.items():
            placeholder = f"{{{key}}}"
            if placeholder in path:
                path = path.replace(placeholder, str(value))

        # Ensure base URL doesn't have trailing slash
        base = self.base_url.rstrip("/")

        return f"{base}{path}"

    def _build_params(self, endpoint: str, **params) -> dict:
        """
        Build query parameters for an endpoint.

        Args:
            endpoint: Endpoint name
            **params: Provided parameters

        Returns:
            Query parameters dict with apikey
        """
        config = self.get_endpoint_config(endpoint)
        if not config:
            return {"apikey": self.api_key}

        allowed_params = config.all_params

        # Always include API key
        query_params = {"apikey": self.api_key}

        # Add allowed parameters
        for param_name in allowed_params:
            if param_name in params and params[param_name] is not None:
                query_params[param_name] = params[param_name]

        return query_params

    def _validate_required_params(self, endpoint: str, **params) -> None:
        """
        Validate required parameters are present.

        Args:
            endpoint: Endpoint name
            **params: Provided parameters

        Raises:
            ValueError: If required parameter is missing
        """
        config = self.get_endpoint_config(endpoint)
        if not config:
            return

        for param in config.required_params:
            if param not in params or params[param] is None:
                raise ValueError(
                    f"Endpoint '{endpoint}' requires parameter: {param}"
                )

    async def fetch(
        self,
        session: aiohttp.ClientSession,
        endpoint: str,
        **params,
    ) -> HttpResponse:
        """
        Fetch data from FMP API.

        Args:
            session: aiohttp ClientSession
            endpoint: API endpoint name
            **params: Endpoint-specific parameters

        Returns:
            HttpResponse with raw API data

        Raises:
            ValueError: If endpoint invalid or required params missing
        """
        if not self.validate_endpoint(endpoint):
            raise ValueError(f"Invalid endpoint: {endpoint}")

        self._validate_required_params(endpoint, **params)

        url = self._build_url(endpoint, **params)
        query_params = self._build_params(endpoint, **params)

        return await self.http_client.get(
            session,
            url,
            params=query_params,
            timeout=self.config.timeout,
        )

    def normalize(self, data: Any, endpoint: str) -> Any:
        """
        Normalize FMP API response.

        Default normalization handles common patterns:
        - Error responses with "Error Message"
        - Single-item list extraction
        - Historical data wrapping

        Override in category modules for specific normalization.

        Args:
            data: Raw API response
            endpoint: Endpoint that was called

        Returns:
            Normalized data
        """
        # Check for error response
        if isinstance(data, dict) and "Error Message" in data:
            return {"error": data["Error Message"], "data": None}

        # Extract single item from list (common pattern)
        if isinstance(data, list) and len(data) == 1:
            # For endpoints that return single items
            config = self.get_endpoint_config(endpoint)
            if config and "symbol" in config.required_params:
                return data[0]

        # Historical data wrapping
        if isinstance(data, dict) and "historical" in data:
            return {
                "symbol": data.get("symbol"),
                "historical": data.get("historical", []),
            }

        return data

    def cache_key(self, endpoint: str, **params) -> str:
        """
        Generate cache key for FMP request.

        Args:
            endpoint: API endpoint
            **params: Request parameters

        Returns:
            Cache key string (without API key)
        """
        # Exclude API key from cache key
        cache_params = {k: v for k, v in params.items() if k != "apikey"}
        return self._generate_cache_key(endpoint, **cache_params)

    def validate_symbol(self, symbol: str) -> bool:
        """
        Validate a stock symbol format.

        Args:
            symbol: Symbol to validate

        Returns:
            True if valid format
        """
        if not symbol:
            return False

        # Basic validation: alphanumeric with . and -, 1-10 chars
        cleaned = symbol.replace(".", "").replace("-", "")
        if not cleaned.isalnum():
            return False

        return len(symbol) <= 10
