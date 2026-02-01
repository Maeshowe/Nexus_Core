"""
OmniData Nexus Core - HTTP Client Layer

Async HTTP client wrapper around aiohttp with timeout handling,
response parsing, and error normalization.
"""

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

import aiohttp


class HttpMethod(Enum):
    """HTTP request methods."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


class HttpError(Exception):
    """Base exception for HTTP-related errors."""

    def __init__(self, message: str, status_code: Optional[int] = None, url: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.url = url


class TimeoutError(HttpError):
    """Request timed out."""

    pass


class RateLimitError(HttpError):
    """Rate limit exceeded (429)."""

    def __init__(self, message: str, retry_after: Optional[int] = None, url: str = ""):
        super().__init__(message, status_code=429, url=url)
        self.retry_after = retry_after


class ServerError(HttpError):
    """Server error (5xx)."""

    pass


class ClientError(HttpError):
    """Client error (4xx, except 429)."""

    pass


class ConnectionError(HttpError):
    """Connection-related error."""

    pass


@dataclass
class HttpResponse:
    """
    Normalized HTTP response container.

    Attributes:
        status: HTTP status code
        data: Parsed response data (JSON or raw text)
        headers: Response headers
        url: Request URL
        elapsed_ms: Request duration in milliseconds
    """

    status: int
    data: Any
    headers: dict
    url: str
    elapsed_ms: float

    @property
    def is_success(self) -> bool:
        """Check if response indicates success (2xx)."""
        return 200 <= self.status < 300

    @property
    def is_rate_limited(self) -> bool:
        """Check if response is a rate limit error."""
        return self.status == 429

    @property
    def is_server_error(self) -> bool:
        """Check if response is a server error (5xx)."""
        return 500 <= self.status < 600


class HttpClient:
    """
    Async HTTP client wrapper for API requests.

    Provides a clean interface around aiohttp with:
    - Configurable timeouts
    - JSON parsing
    - Error normalization
    - Response timing

    Usage:
        client = HttpClient(timeout=30.0)
        async with aiohttp.ClientSession() as session:
            response = await client.get(session, "https://api.example.com/data")
            if response.is_success:
                print(response.data)
    """

    def __init__(
        self,
        timeout: float = 30.0,
        default_headers: Optional[dict] = None,
    ):
        """
        Initialize HTTP client.

        Args:
            timeout: Default request timeout in seconds.
            default_headers: Headers to include in all requests.
        """
        self.timeout = timeout
        self.default_headers = default_headers or {}

    async def close(self) -> None:
        """Close the HTTP client. Currently a no-op as sessions are managed externally."""
        pass

    async def request(
        self,
        session: aiohttp.ClientSession,
        method: HttpMethod,
        url: str,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
        json_data: Optional[dict] = None,
        timeout: Optional[float] = None,
    ) -> HttpResponse:
        """
        Make an HTTP request.

        Args:
            session: aiohttp ClientSession
            method: HTTP method
            url: Request URL
            params: Query parameters
            headers: Additional headers (merged with defaults)
            json_data: JSON body for POST/PUT requests
            timeout: Request timeout (overrides default)

        Returns:
            HttpResponse with parsed data

        Raises:
            TimeoutError: Request timed out
            RateLimitError: Rate limit exceeded (429)
            ServerError: Server error (5xx)
            ClientError: Client error (4xx)
            ConnectionError: Connection failed
        """
        import time

        request_timeout = timeout or self.timeout
        merged_headers = {**self.default_headers, **(headers or {})}

        start_time = time.perf_counter()

        try:
            client_timeout = aiohttp.ClientTimeout(total=request_timeout)

            async with session.request(
                method.value,
                url,
                params=params,
                headers=merged_headers,
                json=json_data,
                timeout=client_timeout,
            ) as response:
                elapsed_ms = (time.perf_counter() - start_time) * 1000

                # Try to parse as JSON, fall back to text
                try:
                    data = await response.json()
                except (aiohttp.ContentTypeError, ValueError):
                    data = await response.text()

                http_response = HttpResponse(
                    status=response.status,
                    data=data,
                    headers=dict(response.headers),
                    url=str(response.url),
                    elapsed_ms=elapsed_ms,
                )

                # Raise exceptions for error status codes
                self._check_response(http_response)

                return http_response

        except asyncio.TimeoutError as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            raise TimeoutError(
                f"Request timed out after {request_timeout}s",
                url=url,
            ) from e

        except aiohttp.ClientConnectorError as e:
            raise ConnectionError(
                f"Connection failed: {e}",
                url=url,
            ) from e

        except aiohttp.ClientError as e:
            raise HttpError(
                f"HTTP client error: {e}",
                url=url,
            ) from e

    def _check_response(self, response: HttpResponse) -> None:
        """
        Check response for error status codes and raise appropriate exceptions.

        Args:
            response: HTTP response to check

        Raises:
            RateLimitError: For 429 status
            ServerError: For 5xx status
            ClientError: For other 4xx status
        """
        if response.is_success:
            return

        if response.is_rate_limited:
            retry_after = response.headers.get("Retry-After")
            retry_seconds = int(retry_after) if retry_after and retry_after.isdigit() else None
            raise RateLimitError(
                "Rate limit exceeded",
                retry_after=retry_seconds,
                url=response.url,
            )

        if response.is_server_error:
            raise ServerError(
                f"Server error: {response.status}",
                status_code=response.status,
                url=response.url,
            )

        if 400 <= response.status < 500:
            raise ClientError(
                f"Client error: {response.status}",
                status_code=response.status,
                url=response.url,
            )

    async def get(
        self,
        session: aiohttp.ClientSession,
        url: str,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
        timeout: Optional[float] = None,
    ) -> HttpResponse:
        """
        Make a GET request.

        Args:
            session: aiohttp ClientSession
            url: Request URL
            params: Query parameters
            headers: Additional headers
            timeout: Request timeout

        Returns:
            HttpResponse with parsed data
        """
        return await self.request(
            session,
            HttpMethod.GET,
            url,
            params=params,
            headers=headers,
            timeout=timeout,
        )

    async def post(
        self,
        session: aiohttp.ClientSession,
        url: str,
        json_data: Optional[dict] = None,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
        timeout: Optional[float] = None,
    ) -> HttpResponse:
        """
        Make a POST request.

        Args:
            session: aiohttp ClientSession
            url: Request URL
            json_data: JSON body
            params: Query parameters
            headers: Additional headers
            timeout: Request timeout

        Returns:
            HttpResponse with parsed data
        """
        return await self.request(
            session,
            HttpMethod.POST,
            url,
            params=params,
            headers=headers,
            json_data=json_data,
            timeout=timeout,
        )
