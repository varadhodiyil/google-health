
"""Shared fixtures for Google Health tests."""

from typing import TYPE_CHECKING

import httpx
import pytest_asyncio

from google_health import GoogleHealthClient
from google_health.config import Settings

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

DISCOVERY_DOCUMENT: dict[str, object] = {
    "rootUrl": "https://health.googleapis.com",
    "servicePath": "",
    "resources": {
        "users": {
            "methods": {
                "getProfile": {
                    "id": "health.users.getProfile",
                    "path": "v4/{name=users/*/profile}",
                    "httpMethod": "GET",
                    "parameters": {
                        "name": {
                            "location": "path",
                            "required": True,
                            "type": "string",
                        },
                    },
                },
            },
        },
    },
}


@pytest_asyncio.fixture
async def client() -> AsyncIterator[
    tuple[GoogleHealthClient, list[httpx.Request]]
]:
    """Provide a client with mocked Discovery and API requests."""
    requests: list[httpx.Request] = []

    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        if "$discovery/rest" in str(request.url):
            return httpx.Response(
                200,
                json=DISCOVERY_DOCUMENT,
            )

        requests.append(request)

        return httpx.Response(
            200,
            json={"ok": True},
        )

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
    ) as http:
        instance = GoogleHealthClient(
            Settings(),
            http_client=http,
        )

        yield instance, requests
