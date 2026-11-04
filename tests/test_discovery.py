
"""Tests for Google API Discovery."""

import httpx
import pytest

from google_health.discovery import Discovery
from google_health.exceptions import (
    DiscoveryError,
    MethodNotFoundError,
)


@pytest.mark.asyncio
async def test_load_discovery() -> None:
    """Test Discovery Document loading."""
    document = {
        "resources": {
            "users": {
                "methods": {
                    "getProfile": {
                        "id": "health.users.getProfile",
                        "path": "v4/users/me/profile",
                        "httpMethod": "GET",
                    },
                },
            },
        },
    }

    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(200, json=document)

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
    ) as http:
        discovery = Discovery(
            http,
            "https://example.com/discovery",
        )

        await discovery.load()

        assert "health.users.getProfile" in discovery.methods


@pytest.mark.asyncio
async def test_discovery_caching() -> None:
    """Test that Discovery is downloaded only once."""
    calls = 0

    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            200,
            json={"resources": {}},
        )

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
    ) as http:
        discovery = Discovery(
            http,
            "https://example.com/discovery",
        )

        await discovery.load()
        await discovery.load()

    assert calls == 1


def test_unknown_method() -> None:
    """Test unknown Discovery methods."""
    discovery = Discovery(
        httpx.AsyncClient(),
    )

    with pytest.raises(MethodNotFoundError):
        discovery.get("invalid.method")


@pytest.mark.asyncio
async def test_invalid_discovery_response() -> None:
    """Test Discovery HTTP error handling."""
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(500)

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
    ) as http:
        discovery = Discovery(
            http,
            "https://example.com/discovery",
        )

        with pytest.raises(DiscoveryError):
            await discovery.load()
