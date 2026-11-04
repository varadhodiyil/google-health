
"""Tests for HTTPX transport."""
import httpx
import pytest
from pydantic import SecretStr

from google_health.auth import BearerAuth
from google_health.exceptions import (
    APIError,
    AuthenticationError,
)
from google_health.transport import Transport


@pytest.mark.asyncio
async def test_bearer_authentication() -> None:
    """Test bearer-token authentication headers."""
    requests: list[httpx.Request] = []

    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"ok": True})

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
    ) as http:
        transport = Transport(
            BearerAuth(SecretStr("test-token")),
            http,
        )

        await transport.request(
            "GET",
            "https://example.com/test",
        )

    assert (
        requests[0].headers["Authorization"]
        == "Bearer test-token"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [401, 403])
async def test_authentication_errors(
    status: int,
) -> None:
    """Test authentication failures."""
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(status)

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
    ) as http:
        transport = Transport(
            BearerAuth(SecretStr("test-token")),
            http,
        )

        with pytest.raises(AuthenticationError):
            await transport.request(
                "GET",
                "https://example.com/test",
            )


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [400, 404, 429, 500])
async def test_api_errors(
    status: int,
) -> None:
    """Test unsuccessful API responses."""
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            status,
            json={"error": "test"},
        )

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
    ) as http:
        transport = Transport(
            BearerAuth(SecretStr("test-token")),
            http,
        )

        with pytest.raises(APIError) as error:
            await transport.request(
                "GET",
                "https://example.com/test",
            )

        assert error.value.status_code == status
