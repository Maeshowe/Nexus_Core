"""
OmniData Nexus Core - FRED Provider

Federal Reserve Economic Data (FRED) API provider for
macroeconomic time series data.
"""

from typing import Any, Optional

import aiohttp

from ..http_client import HttpResponse
from .base import BaseDataProvider


class FREDProvider(BaseDataProvider):
    """
    FRED (Federal Reserve Economic Data) provider.

    Supports 32 macroeconomic series across categories:
    - Inflation: CPI, PCE, PPI, Core CPI
    - Labor Market: Unemployment, Payrolls, LFPR, Wages
    - GDP & Growth: GDP, GDI, Industrial Production
    - Housing: Case-Shiller, Housing Starts, Permits
    - Interest Rates: Fed Funds, Treasury Yields
    - Money & Credit: M2, Consumer Credit
    - Financial Conditions: VIX, Yield Curve
    - Leading Indicators: LEI, Consumer Sentiment

    Usage:
        provider = FREDProvider(config, http_client, cache, health_monitor)
        async with aiohttp.ClientSession() as session:
            response = await provider.get(session, "series", series_id="CPIAUCSL")
            print(response.data)
    """

    # Supported FRED series organized by category
    SERIES = {
        # Inflation
        "CPIAUCSL": "Consumer Price Index",
        "CPILFESL": "Core CPI (Less Food and Energy)",
        "PCEPI": "PCE Price Index",
        "PCEPILFE": "Core PCE Price Index",
        "PPIFIS": "Producer Price Index",
        # Labor Market
        "UNRATE": "Unemployment Rate",
        "PAYEMS": "Nonfarm Payrolls",
        "CIVPART": "Labor Force Participation Rate",
        "AHETPI": "Average Hourly Earnings",
        "ICSA": "Initial Jobless Claims",
        "CCSA": "Continued Jobless Claims",
        "JTSJOL": "Job Openings (JOLTS)",
        # GDP & Growth
        "GDP": "Gross Domestic Product",
        "GDPC1": "Real GDP",
        "GDI": "Gross Domestic Income",
        "INDPRO": "Industrial Production Index",
        "UMCSENT": "Consumer Sentiment (UMich)",
        # Housing
        "CSUSHPINSA": "Case-Shiller Home Price Index",
        "HOUST": "Housing Starts",
        "PERMIT": "Building Permits",
        "HSN1F": "New Home Sales",
        "EXHOSLUSM495S": "Existing Home Sales",
        # Interest Rates
        "FEDFUNDS": "Federal Funds Rate",
        "DFF": "Effective Federal Funds Rate",
        "DGS2": "2-Year Treasury Yield",
        "DGS10": "10-Year Treasury Yield",
        "DGS30": "30-Year Treasury Yield",
        "T10Y2Y": "10Y-2Y Treasury Spread",
        "T10Y3M": "10Y-3M Treasury Spread",
        # Money & Credit
        "M2SL": "M2 Money Supply",
        "TOTALSL": "Consumer Credit",
        # Financial Conditions
        "VIXCLS": "VIX Volatility Index",
    }

    # Endpoint configurations
    ENDPOINTS = {
        "series": {
            "path": "/series/observations",
            "params": ["series_id", "observation_start", "observation_end",
                      "units", "frequency", "aggregation_method", "sort_order",
                      "limit", "offset"],
        },
        "series_info": {
            "path": "/series",
            "params": ["series_id"],
        },
        "releases": {
            "path": "/releases",
            "params": ["limit", "offset", "order_by", "sort_order"],
        },
    }

    @property
    def provider_name(self) -> str:
        return "fred"

    def get_supported_endpoints(self) -> list[str]:
        return list(self.ENDPOINTS.keys())

    def get_supported_series(self) -> dict[str, str]:
        """Get dictionary of supported series IDs and descriptions."""
        return self.SERIES.copy()

    def _build_url(self, endpoint: str, **params) -> str:
        """
        Build the full URL for an endpoint.

        Args:
            endpoint: Endpoint name
            **params: Parameters

        Returns:
            Full URL string
        """
        endpoint_config = self.ENDPOINTS.get(endpoint)
        if not endpoint_config:
            raise ValueError(f"Unknown endpoint: {endpoint}")

        path = endpoint_config["path"]
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

        # FRED requires api_key (must be lowercase) and file_type
        query_params = {
            "api_key": self.api_key.lower(),
            "file_type": "json",
        }

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
        Fetch data from FRED API.

        Args:
            session: aiohttp ClientSession
            endpoint: API endpoint name (series, series_info, releases)
            **params: Endpoint-specific parameters

        Returns:
            HttpResponse with raw API data

        Raises:
            ValueError: If endpoint is invalid or required params missing
            HttpError: For HTTP-related errors
        """
        if not self.validate_endpoint(endpoint):
            raise ValueError(f"Invalid endpoint: {endpoint}")

        # Series endpoints require series_id
        if endpoint in ("series", "series_info") and "series_id" not in params:
            raise ValueError(f"Endpoint '{endpoint}' requires 'series_id' parameter")

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
        Normalize FRED API response.

        FRED responses have a standard structure:
        - observations: Array of data points (for series)
        - seriess: Array of series info (for series_info)
        - releases: Array of releases (for releases)

        Args:
            data: Raw API response
            endpoint: Endpoint that was called

        Returns:
            Normalized data structure
        """
        # Check for error response
        if isinstance(data, dict) and "error_code" in data:
            return {
                "error": data.get("error_message", "Unknown error"),
                "error_code": data.get("error_code"),
                "data": None,
            }

        if endpoint == "series":
            if isinstance(data, dict):
                return {
                    "realtime_start": data.get("realtime_start"),
                    "realtime_end": data.get("realtime_end"),
                    "observation_start": data.get("observation_start"),
                    "observation_end": data.get("observation_end"),
                    "units": data.get("units"),
                    "output_type": data.get("output_type"),
                    "order_by": data.get("order_by"),
                    "sort_order": data.get("sort_order"),
                    "count": data.get("count", 0),
                    "observations": data.get("observations", []),
                }
            return data

        if endpoint == "series_info":
            if isinstance(data, dict):
                seriess = data.get("seriess", [])
                # Return single series info if only one
                if len(seriess) == 1:
                    return seriess[0]
                return {"seriess": seriess}
            return data

        if endpoint == "releases":
            if isinstance(data, dict):
                return {
                    "releases": data.get("releases", []),
                    "count": data.get("count", 0),
                }
            return data

        # Default: return as-is
        return data

    def cache_key(self, endpoint: str, **params) -> str:
        """
        Generate cache key for FRED request.

        Args:
            endpoint: API endpoint
            **params: Request parameters

        Returns:
            Cache key string
        """
        # Exclude API key from cache key
        cache_params = {k: v for k, v in params.items() if k != "api_key"}
        return self._generate_cache_key(endpoint, **cache_params)

    def validate_series_id(self, series_id: str) -> bool:
        """
        Validate a FRED series ID.

        Args:
            series_id: Series ID to validate

        Returns:
            True if valid format (alphanumeric, uppercase)
        """
        if not series_id:
            return False

        # FRED series IDs are uppercase alphanumeric with some special chars
        return series_id.replace("_", "").isalnum()

    def is_supported_series(self, series_id: str) -> bool:
        """
        Check if a series ID is in our predefined list.

        Args:
            series_id: Series ID to check

        Returns:
            True if in supported list
        """
        return series_id.upper() in self.SERIES

    async def get_series(
        self,
        session: aiohttp.ClientSession,
        series_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        use_cache: bool = True,
    ):
        """
        Convenience method to fetch a specific series.

        Args:
            session: aiohttp ClientSession
            series_id: FRED series ID (e.g., "CPIAUCSL")
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)
            use_cache: Whether to use caching

        Returns:
            ProviderResponse with series data
        """
        params = {"series_id": series_id}
        if start_date:
            params["observation_start"] = start_date
        if end_date:
            params["observation_end"] = end_date

        return await self.get(session, "series", use_cache=use_cache, **params)


# Convenience function to create provider with minimal config
def create_fred_provider(
    api_key: str,
    cache_dir: Optional[str] = None,
    timeout: float = 30.0,
) -> FREDProvider:
    """
    Create a FRED provider with default configuration.

    Args:
        api_key: FRED API key
        cache_dir: Optional cache directory path
        timeout: Request timeout in seconds

    Returns:
        Configured FREDProvider instance
    """
    from pathlib import Path

    from ..cache import CacheManager
    from ..config import ProviderConfig
    from ..health import HealthMonitor
    from ..http_client import HttpClient

    config = ProviderConfig(
        api_key=api_key,
        base_url="https://api.stlouisfed.org/fred",
        max_concurrency=1,  # FRED is rate-limited
        timeout=timeout,
    )

    http_client = HttpClient(timeout=timeout)

    cache_path = Path(cache_dir) if cache_dir else Path.cwd() / "data" / "cache"
    cache = CacheManager(base_dir=cache_path)

    health_monitor = HealthMonitor()

    return FREDProvider(
        config=config,
        http_client=http_client,
        cache=cache,
        health_monitor=health_monitor,
    )
