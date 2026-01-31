"""
OmniData Nexus Core - Polygon Provider

Polygon.io API provider with 4 endpoints for market data,
trades, and options snapshots.
"""

from typing import Any, Optional

import aiohttp

from ..http_client import HttpResponse
from .base import BaseDataProvider


class PolygonProvider(BaseDataProvider):
    """
    Polygon.io data provider.

    Supports 4 endpoints:
    - aggs_daily: Daily aggregate bars (OHLCV)
    - trades: Trade-level data
    - options_snapshot: Options chain snapshot
    - market_snapshot: Market-wide snapshot

    Usage:
        provider = PolygonProvider(config, http_client, cache, health_monitor)
        async with aiohttp.ClientSession() as session:
            response = await provider.get(
                session, "aggs_daily",
                symbol="SPY", start="2024-01-01", end="2024-01-31"
            )
            print(response.data)
    """

    # Endpoint configurations
    ENDPOINTS = {
        "aggs_daily": {
            "path": "/v2/aggs/ticker/{symbol}/range/1/day/{start}/{end}",
            "params": ["adjusted", "sort", "limit"],
        },
        "trades": {
            "path": "/v3/trades/{symbol}",
            "params": ["timestamp", "timestamp.gte", "timestamp.lte",
                      "order", "limit", "sort"],
        },
        "options_snapshot": {
            "path": "/v3/snapshot/options/{underlyingAsset}",
            "params": ["strike_price", "expiration_date", "contract_type",
                      "order", "limit", "sort"],
        },
        "market_snapshot": {
            "path": "/v2/snapshot/locale/us/markets/stocks/tickers",
            "params": ["tickers", "include_otc"],
        },
    }

    @property
    def provider_name(self) -> str:
        return "polygon"

    def get_supported_endpoints(self) -> list[str]:
        return list(self.ENDPOINTS.keys())

    def _build_url(self, endpoint: str, **params) -> str:
        """
        Build the full URL for an endpoint.

        Args:
            endpoint: Endpoint name
            **params: Parameters including path variables

        Returns:
            Full URL string
        """
        endpoint_config = self.ENDPOINTS.get(endpoint)
        if not endpoint_config:
            raise ValueError(f"Unknown endpoint: {endpoint}")

        path = endpoint_config["path"]

        # Replace path parameters
        if "{symbol}" in path:
            symbol = params.get("symbol")
            if not symbol:
                raise ValueError(f"Endpoint '{endpoint}' requires 'symbol' parameter")
            path = path.replace("{symbol}", symbol)

        if "{underlyingAsset}" in path:
            asset = params.get("underlyingAsset") or params.get("symbol")
            if not asset:
                raise ValueError(f"Endpoint '{endpoint}' requires 'underlyingAsset' or 'symbol' parameter")
            path = path.replace("{underlyingAsset}", asset)

        if "{start}" in path:
            start = params.get("start")
            if not start:
                raise ValueError(f"Endpoint '{endpoint}' requires 'start' parameter")
            path = path.replace("{start}", start)

        if "{end}" in path:
            end = params.get("end")
            if not end:
                raise ValueError(f"Endpoint '{endpoint}' requires 'end' parameter")
            path = path.replace("{end}", end)

        return f"{self.base_url}{path}"

    def _build_params(self, endpoint: str, **params) -> dict:
        """
        Build query parameters for an endpoint.

        Args:
            endpoint: Endpoint name
            **params: All provided parameters

        Returns:
            Dictionary of query parameters
        """
        endpoint_config = self.ENDPOINTS.get(endpoint, {})
        allowed_params = endpoint_config.get("params", [])

        # Always include API key
        query_params = {"apiKey": self.api_key}

        # Add allowed parameters
        for param_name in allowed_params:
            if param_name in params and params[param_name] is not None:
                query_params[param_name] = params[param_name]

        return query_params

    async def fetch(
        self,
        session: aiohttp.ClientSession,
        endpoint: str,
        **params,
    ) -> HttpResponse:
        """
        Fetch data from Polygon API.

        Args:
            session: aiohttp ClientSession
            endpoint: API endpoint name
            **params: Endpoint-specific parameters

        Returns:
            HttpResponse with raw API data

        Raises:
            ValueError: If endpoint is invalid or required params missing
            HttpError: For HTTP-related errors
        """
        if not self.validate_endpoint(endpoint):
            raise ValueError(f"Invalid endpoint: {endpoint}")

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
        Normalize Polygon API response.

        Polygon responses have a standard structure:
        - status: "OK" or error
        - results: The actual data (array or object)
        - request_id: Request identifier

        Args:
            data: Raw API response
            endpoint: Endpoint that was called

        Returns:
            Normalized data structure
        """
        # Check for error response
        if isinstance(data, dict):
            status = data.get("status", "").upper()
            if status == "ERROR":
                return {
                    "error": data.get("error", "Unknown error"),
                    "message": data.get("message"),
                    "data": None,
                }

        # Extract results based on endpoint
        if endpoint == "aggs_daily":
            if isinstance(data, dict):
                return {
                    "ticker": data.get("ticker"),
                    "queryCount": data.get("queryCount", 0),
                    "resultsCount": data.get("resultsCount", 0),
                    "adjusted": data.get("adjusted", False),
                    "results": data.get("results", []),
                }
            return data

        if endpoint == "trades":
            if isinstance(data, dict):
                return {
                    "results": data.get("results", []),
                    "next_url": data.get("next_url"),
                }
            return data

        if endpoint == "options_snapshot":
            if isinstance(data, dict):
                return {
                    "results": data.get("results", []),
                    "next_url": data.get("next_url"),
                }
            return data

        if endpoint == "market_snapshot":
            if isinstance(data, dict):
                return {
                    "tickers": data.get("tickers", []),
                    "count": data.get("count", 0),
                }
            return data

        # Default: return as-is
        return data

    def cache_key(self, endpoint: str, **params) -> str:
        """
        Generate cache key for Polygon request.

        Args:
            endpoint: API endpoint
            **params: Request parameters

        Returns:
            Cache key string
        """
        # Exclude API key from cache key
        cache_params = {k: v for k, v in params.items() if k != "apiKey"}
        return self._generate_cache_key(endpoint, **cache_params)

    def validate_symbol(self, symbol: str) -> bool:
        """
        Validate a stock/options symbol.

        Args:
            symbol: Symbol to validate

        Returns:
            True if valid format
        """
        if not symbol:
            return False

        # Basic validation: alphanumeric with allowed special chars
        allowed_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-:")
        if not all(c in allowed_chars for c in symbol.upper()):
            return False

        if len(symbol) > 21:  # Options symbols can be long
            return False

        return True


# Convenience function to create provider with minimal config
def create_polygon_provider(
    api_key: str,
    cache_dir: Optional[str] = None,
    timeout: float = 30.0,
) -> PolygonProvider:
    """
    Create a Polygon provider with default configuration.

    Args:
        api_key: Polygon API key
        cache_dir: Optional cache directory path
        timeout: Request timeout in seconds

    Returns:
        Configured PolygonProvider instance
    """
    from pathlib import Path

    from ..cache import CacheManager
    from ..config import ProviderConfig
    from ..health import HealthMonitor
    from ..http_client import HttpClient

    config = ProviderConfig(
        api_key=api_key,
        base_url="https://api.polygon.io",
        max_concurrency=10,
        timeout=timeout,
    )

    http_client = HttpClient(timeout=timeout)

    cache_path = Path(cache_dir) if cache_dir else Path.cwd() / "data" / "cache"
    cache = CacheManager(base_dir=cache_path)

    health_monitor = HealthMonitor()

    return PolygonProvider(
        config=config,
        http_client=http_client,
        cache=cache,
        health_monitor=health_monitor,
    )
