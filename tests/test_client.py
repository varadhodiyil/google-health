
"""Tests for the public Google Health client."""
from typing import TYPE_CHECKING

import pytest
from pydantic import SecretStr

from google_health import (
    GoogleHealthClient,
    MethodNotFoundError,
)
from google_health.client import _build_url
from google_health.config import Settings

if TYPE_CHECKING:
    import httpx


@pytest.mark.asyncio
async def test_discovered_methods(
    client: tuple[
        GoogleHealthClient,
        list[httpx.Request],
    ],
) -> None:
    """Test discovery of API methods."""
    instance, _ = client

    await instance.discovery.load()

    assert "health.users.getProfile" in instance.methods


@pytest.mark.asyncio
async def test_profile_request(
    client: tuple[
        GoogleHealthClient,
        list[httpx.Request],
    ],
) -> None:
    """Test profile endpoint URL construction."""
    instance, requests = client

    result = await instance.call(
        "health.users.getProfile",
        name="users/me/profile",
    )

    assert result == {"ok": True}
    assert len(requests) == 1

    assert requests[0].url.path == (
        "/v4/users/me/profile"
    )


@pytest.mark.parametrize(
    ("root", "service", "path", "expected"),
    [
        (
            "https://health.googleapis.com/",
            "",
            "v4/users/me/profile",
            "https://health.googleapis.com/v4/users/me/profile",
        ),
        (
            "https://health.googleapis.com",
            "",
            "/v4/users/me/profile",
            "https://health.googleapis.com/v4/users/me/profile",
        ),
        (
            "https://health.googleapis.com/",
            "v4/",
            "users/me/profile",
            "https://health.googleapis.com/v4/users/me/profile",
        ),
        (
            "https://health.googleapis.com",
            "/v4/",
            "/users/me/profile",
            "https://health.googleapis.com/v4/users/me/profile",
        ),
    ],
)
def test_build_url(
    root: str,
    service: str,
    path: str,
    expected: str,
) -> None:
    """Test URL construction with different separators."""
    assert _build_url(root, service, path) == expected

@pytest.mark.asyncio
async def test_unknown_method(
    client: tuple[
        GoogleHealthClient,
        list[httpx.Request],
    ],
) -> None:
    """Test unknown API method handling."""
    instance, _ = client

    await instance.discovery.load()

    with pytest.raises(MethodNotFoundError):
        instance.discovery.get("invalid.method")


def test_empty_token_rejected() -> None:
    """Test empty OAuth token validation."""
    settings = Settings(
        client_id="test-client",
        client_secret=SecretStr("test-secret"),
        access_token=SecretStr(""),
    )

    with pytest.raises(ValueError):
        GoogleHealthClient(settings)
