"""
OmniData Nexus Core - FMP Provider

Financial Modeling Prep API provider with 13 endpoints for
fundamental data, financials, and insider trading.
"""

from typing import Any, Optional

import aiohttp

from ..http_client import HttpResponse
from .base import BaseDataProvider


class FMPProvider(BaseDataProvider):
    """
    FMP (Financial Modeling Prep) data provider.

    Supports 13 endpoints:
    - screener: Stock screener
    - profile: Company profile
    - quote: Real-time quote
    - historical_price: Historical daily prices
    - earnings_calendar: Earnings announcements
    - balance_sheet: Balance sheet statements
    - income_statement: Income statements
    - cash_flow: Cash flow statements
    - ratios: Financial ratios
    - growth: Financial growth metrics
    - key_metrics: Key financial metrics
    - insider_trading: Insider transactions
    - institutional_ownership: Institutional holdings

    Usage:
        provider = FMPProvider(config, http_client, cache, health_monitor)
        async with aiohttp.ClientSession() as session:
            response = await provider.get(session, "profile", symbol="AAPL")
            print(response.data)
    """

    # Endpoint configurations (updated to new /stable/ API - August 2025)
    ENDPOINTS = {
        "screener": {
            "path": "/stable/company-screener",
            "params": ["marketCapMoreThan", "marketCapLowerThan", "priceMoreThan",
                      "priceLowerThan", "betaMoreThan", "betaLowerThan",
                      "volumeMoreThan", "volumeLowerThan", "dividendMoreThan",
                      "dividendLowerThan", "isEtf", "isActivelyTrading",
                      "sector", "industry", "country", "exchange", "limit"],
        },
        "profile": {
            "path": "/stable/profile",
            "params": ["symbol"],
        },
        "quote": {
            "path": "/stable/quote",
            "params": ["symbol"],
        },
        "historical_price": {
            "path": "/stable/historical-price-eod/full",
            "params": ["symbol", "from", "to"],
        },
        "earnings_calendar": {
            "path": "/stable/earnings-calendar",
            "params": ["symbol", "from", "to"],
        },
        "balance_sheet": {
            "path": "/stable/balance-sheet-statement",
            "params": ["symbol", "period", "limit"],
        },
        "income_statement": {
            "path": "/stable/income-statement",
            "params": ["symbol", "period", "limit"],
        },
        "cash_flow": {
            "path": "/stable/cash-flow-statement",
            "params": ["symbol", "period", "limit"],
        },
        "ratios": {
            "path": "/stable/ratios",
            "params": ["symbol", "period", "limit"],
        },
        "growth": {
            "path": "/stable/financial-growth",
            "params": ["symbol", "period", "limit"],
        },
        "key_metrics": {
            "path": "/stable/key-metrics",
            "params": ["symbol", "period", "limit"],
        },
        "insider_trading": {
            "path": "/stable/insider-trading/search",
            "params": ["symbol", "page", "limit"],
        },
        "institutional_ownership": {
            "path": "/stable/institutional-ownership/latest",
            "params": ["symbol"],
        },
    }

    @property
    def provider_name(self) -> str:
        return "fmp"

    def get_supported_endpoints(self) -> list[str]:
        return list(self.ENDPOINTS.keys())

    def _build_url(self, endpoint: str, **params) -> str:
        """
        Build the full URL for an endpoint.

        Args:
            endpoint: Endpoint name
            **params: Parameters including symbol if needed

        Returns:
            Full URL string
        """
        endpoint_config = self.ENDPOINTS.get(endpoint)
        if not endpoint_config:
            raise ValueError(f"Unknown endpoint: {endpoint}")

        path = endpoint_config["path"]

        # Replace path parameters (e.g., {symbol})
        if "{symbol}" in path:
            symbol = params.get("symbol")
            if not symbol:
                raise ValueError(f"Endpoint '{endpoint}' requires 'symbol' parameter")
            path = path.replace("{symbol}", symbol)

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
        query_params = {"apikey": self.api_key}

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
        Fetch data from FMP API.

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
        Normalize FMP API response.

        FMP responses vary by endpoint:
        - Most return a list of objects
        - Some wrap data in a dict
        - Error responses have an "Error Message" field

        Args:
            data: Raw API response
            endpoint: Endpoint that was called

        Returns:
            Normalized data structure
        """
        # Check for error response
        if isinstance(data, dict) and "Error Message" in data:
            return {"error": data["Error Message"], "data": None}

        # Normalize based on endpoint type
        if endpoint == "historical_price":
            # Historical prices come wrapped in {"symbol": ..., "historical": [...]}
            if isinstance(data, dict) and "historical" in data:
                return {
                    "symbol": data.get("symbol"),
                    "historical": data.get("historical", []),
                }
            return data

        if endpoint == "profile":
            # Profile returns a list with single item, extract it
            if isinstance(data, list) and len(data) == 1:
                return data[0]
            return data

        if endpoint == "quote":
            # Quote returns a list with single item, extract it
            if isinstance(data, list) and len(data) == 1:
                return data[0]
            return data

        # Default: return as-is (most endpoints return lists)
        return data

    def cache_key(self, endpoint: str, **params) -> str:
        """
        Generate cache key for FMP request.

        Cache key format: endpoint_param1=value1_param2=value2

        Args:
            endpoint: API endpoint
            **params: Request parameters

        Returns:
            Cache key string
        """
        # Exclude API key from cache key
        cache_params = {k: v for k, v in params.items() if k != "apikey"}
        return self._generate_cache_key(endpoint, **cache_params)

    def validate_symbol(self, symbol: str) -> bool:
        """
        Validate a stock symbol.

        Args:
            symbol: Stock symbol to validate

        Returns:
            True if valid format
        """
        if not symbol:
            return False

        # Basic validation: alphanumeric, 1-10 chars
        if not symbol.replace(".", "").replace("-", "").isalnum():
            return False

        if len(symbol) > 10:
            return False

        return True


# Convenience function to create provider with minimal config
def create_fmp_provider(
    api_key: str,
    cache_dir: Optional[str] = None,
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

    from ..cache import CacheManager
    from ..config import ProviderConfig
    from ..health import HealthMonitor
    from ..http_client import HttpClient

    config = ProviderConfig(
        api_key=api_key,
        base_url="https://financialmodelingprep.com/api",
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
