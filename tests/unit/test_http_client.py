"""
Unit tests for the HTTP client layer.
"""

import asyncio

import pytest
from aioresponses import aioresponses

import aiohttp

from data_loader.http_client import (
    ClientError,
    ConnectionError,
    HttpClient,
    HttpError,
    HttpMethod,
    HttpResponse,
    RateLimitError,
    ServerError,
    TimeoutError,
)


@pytest.mark.unit
class TestHttpMethod:
    """Tests for HttpMethod enum."""

    def test_all_methods(self):
        assert HttpMethod.GET.value == "GET"
        assert HttpMethod.POST.value == "POST"
        assert HttpMethod.PUT.value == "PUT"
        assert HttpMethod.DELETE.value == "DELETE"


@pytest.mark.unit
class TestHttpError:
    """Tests for HTTP error classes."""

    def test_http_error_base(self):
        error = HttpError("Test error", status_code=400, url="https://example.com")
        assert str(error) == "Test error"
        assert error.status_code == 400
        assert error.url == "https://example.com"

    def test_timeout_error(self):
        error = TimeoutError("Request timed out", url="https://example.com")
        assert isinstance(error, HttpError)
        assert error.url == "https://example.com"

    def test_rate_limit_error(self):
        error = RateLimitError("Rate limited", retry_after=60, url="https://example.com")
        assert isinstance(error, HttpError)
        assert error.status_code == 429
        assert error.retry_after == 60

    def test_server_error(self):
        error = ServerError("Server down", status_code=500, url="https://example.com")
        assert isinstance(error, HttpError)
        assert error.status_code == 500

    def test_client_error(self):
        error = ClientError("Bad request", status_code=400, url="https://example.com")
        assert isinstance(error, HttpError)
        assert error.status_code == 400


@pytest.mark.unit
class TestHttpResponse:
    """Tests for HttpResponse dataclass."""

    def test_create_response(self):
        response = HttpResponse(
            status=200,
            data={"key": "value"},
            headers={"Content-Type": "application/json"},
            url="https://example.com/api",
            elapsed_ms=150.5,
        )
        assert response.status == 200
        assert response.data == {"key": "value"}
        assert response.headers == {"Content-Type": "application/json"}
        assert response.url == "https://example.com/api"
        assert response.elapsed_ms == 150.5

    def test_is_success_200(self):
        response = HttpResponse(200, {}, {}, "", 0)
        assert response.is_success is True

    def test_is_success_201(self):
        response = HttpResponse(201, {}, {}, "", 0)
        assert response.is_success is True

    def test_is_success_299(self):
        response = HttpResponse(299, {}, {}, "", 0)
        assert response.is_success is True

    def test_is_not_success_400(self):
        response = HttpResponse(400, {}, {}, "", 0)
        assert response.is_success is False

    def test_is_not_success_500(self):
        response = HttpResponse(500, {}, {}, "", 0)
        assert response.is_success is False

    def test_is_rate_limited(self):
        response = HttpResponse(429, {}, {}, "", 0)
        assert response.is_rate_limited is True

    def test_is_not_rate_limited(self):
        response = HttpResponse(200, {}, {}, "", 0)
        assert response.is_rate_limited is False

    def test_is_server_error(self):
        response = HttpResponse(500, {}, {}, "", 0)
        assert response.is_server_error is True

    def test_is_server_error_503(self):
        response = HttpResponse(503, {}, {}, "", 0)
        assert response.is_server_error is True

    def test_is_not_server_error(self):
        response = HttpResponse(400, {}, {}, "", 0)
        assert response.is_server_error is False


@pytest.mark.unit
class TestHttpClient:
    """Tests for HttpClient class."""

    def test_init_default(self):
        client = HttpClient()
        assert client.timeout == 30.0
        assert client.default_headers == {}

    def test_init_custom(self):
        client = HttpClient(
            timeout=60.0,
            default_headers={"Authorization": "Bearer token"},
        )
        assert client.timeout == 60.0
        assert client.default_headers == {"Authorization": "Bearer token"}

    @pytest.mark.asyncio
    async def test_get_success(self):
        client = HttpClient()
        url = "https://api.example.com/data"

        with aioresponses() as m:
            m.get(url, payload={"result": "success"}, status=200)

            async with aiohttp.ClientSession() as session:
                response = await client.get(session, url)

                assert response.status == 200
                assert response.data == {"result": "success"}
                assert response.is_success is True

    @pytest.mark.asyncio
    async def test_get_with_params(self):
        client = HttpClient()
        # Include params in the URL for aioresponses matching
        url = "https://api.example.com/data?filter=active"

        with aioresponses() as m:
            m.get(url, payload={"result": "filtered"}, status=200)

            async with aiohttp.ClientSession() as session:
                response = await client.get(
                    session, "https://api.example.com/data", params={"filter": "active"}
                )

                assert response.status == 200
                assert response.data == {"result": "filtered"}

    @pytest.mark.asyncio
    async def test_get_with_headers(self):
        client = HttpClient(default_headers={"X-Default": "value"})
        url = "https://api.example.com/data"

        with aioresponses() as m:
            m.get(url, payload={}, status=200)

            async with aiohttp.ClientSession() as session:
                response = await client.get(
                    session, url, headers={"X-Custom": "custom"}
                )

                assert response.status == 200

    @pytest.mark.asyncio
    async def test_post_success(self):
        client = HttpClient()
        url = "https://api.example.com/data"

        with aioresponses() as m:
            m.post(url, payload={"id": 123}, status=201)

            async with aiohttp.ClientSession() as session:
                response = await client.post(
                    session, url, json_data={"name": "test"}
                )

                assert response.status == 201
                assert response.data == {"id": 123}

    @pytest.mark.asyncio
    async def test_rate_limit_error(self):
        client = HttpClient()
        url = "https://api.example.com/data"

        with aioresponses() as m:
            m.get(url, status=429, headers={"Retry-After": "60"})

            async with aiohttp.ClientSession() as session:
                with pytest.raises(RateLimitError) as exc_info:
                    await client.get(session, url)

                assert exc_info.value.status_code == 429
                assert exc_info.value.retry_after == 60

    @pytest.mark.asyncio
    async def test_rate_limit_no_retry_after(self):
        client = HttpClient()
        url = "https://api.example.com/data"

        with aioresponses() as m:
            m.get(url, status=429)

            async with aiohttp.ClientSession() as session:
                with pytest.raises(RateLimitError) as exc_info:
                    await client.get(session, url)

                assert exc_info.value.retry_after is None

    @pytest.mark.asyncio
    async def test_server_error_500(self):
        client = HttpClient()
        url = "https://api.example.com/data"

        with aioresponses() as m:
            m.get(url, status=500, body="Internal Server Error")

            async with aiohttp.ClientSession() as session:
                with pytest.raises(ServerError) as exc_info:
                    await client.get(session, url)

                assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_server_error_503(self):
        client = HttpClient()
        url = "https://api.example.com/data"

        with aioresponses() as m:
            m.get(url, status=503)

            async with aiohttp.ClientSession() as session:
                with pytest.raises(ServerError) as exc_info:
                    await client.get(session, url)

                assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_client_error_400(self):
        client = HttpClient()
        url = "https://api.example.com/data"

        with aioresponses() as m:
            m.get(url, status=400, payload={"error": "Bad Request"})

            async with aiohttp.ClientSession() as session:
                with pytest.raises(ClientError) as exc_info:
                    await client.get(session, url)

                assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_client_error_404(self):
        client = HttpClient()
        url = "https://api.example.com/data"

        with aioresponses() as m:
            m.get(url, status=404)

            async with aiohttp.ClientSession() as session:
                with pytest.raises(ClientError) as exc_info:
                    await client.get(session, url)

                assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_timeout_error(self):
        client = HttpClient(timeout=0.001)  # Very short timeout
        url = "https://api.example.com/data"

        with aioresponses() as m:
            m.get(url, exception=asyncio.TimeoutError())

            async with aiohttp.ClientSession() as session:
                with pytest.raises(TimeoutError):
                    await client.get(session, url)

    @pytest.mark.asyncio
    async def test_connection_error(self):
        client = HttpClient()
        url = "https://api.example.com/data"

        # Create a mock connection key for aiohttp
        from unittest.mock import MagicMock

        mock_key = MagicMock()
        mock_key.ssl = False

        with aioresponses() as m:
            m.get(url, exception=aiohttp.ClientConnectorError(
                connection_key=mock_key, os_error=OSError("Connection refused")
            ))

            async with aiohttp.ClientSession() as session:
                with pytest.raises(ConnectionError):
                    await client.get(session, url)

    @pytest.mark.asyncio
    async def test_text_response(self):
        client = HttpClient()
        url = "https://api.example.com/data"

        with aioresponses() as m:
            m.get(
                url,
                body="Plain text response",
                status=200,
                headers={"Content-Type": "text/plain"},
            )

            async with aiohttp.ClientSession() as session:
                response = await client.get(session, url)

                assert response.status == 200
                assert response.data == "Plain text response"

    @pytest.mark.asyncio
    async def test_elapsed_time_recorded(self):
        client = HttpClient()
        url = "https://api.example.com/data"

        with aioresponses() as m:
            m.get(url, payload={}, status=200)

            async with aiohttp.ClientSession() as session:
                response = await client.get(session, url)

                assert response.elapsed_ms >= 0

    @pytest.mark.asyncio
    async def test_custom_timeout_override(self):
        client = HttpClient(timeout=30.0)
        url = "https://api.example.com/data"

        with aioresponses() as m:
            m.get(url, payload={}, status=200)

            async with aiohttp.ClientSession() as session:
                # Should succeed with explicit timeout
                response = await client.get(session, url, timeout=60.0)
                assert response.is_success
