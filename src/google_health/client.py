"""Asynchronous Google Health API client."""

from typing import TYPE_CHECKING, Self

import httpx

from .auth import BearerAuth
from .discovery import Discovery
from .exceptions import GoogleHealthError
from .transport import Transport
from .utils import resolve_path, resolve_query

if TYPE_CHECKING:
    from .config import Settings


def _build_url(
    root: str,
    service: str,
    path: str,
) -> str:
    """Build an API URL without duplicate separators."""
    parts = [
        root.rstrip("/"),
        service.strip("/"),
        path.lstrip("/"),
    ]

    return "/".join(part for part in parts if part)


class GoogleHealthClient:
    """Asynchronous Google Health API client."""

    def __init__(
        self,
        settings: Settings,
        *,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.settings = settings
        self.http = http_client or httpx.AsyncClient(
            timeout=settings.timeout,
        )

        self._owns_http = http_client is None

        self.auth = BearerAuth(settings.access_token)

        self.discovery = Discovery(self.http)

        self.transport = Transport(
            self.auth,
            self.http,
        )

    async def __aenter__(self) -> Self:
        """Load available API methods."""
        await self.discovery.load()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: object,
    ) -> None:
        """Close the client."""
        await self.aclose()

    async def aclose(self) -> None:
        """Close the HTTP client if owned by this instance."""
        if self._owns_http:
            await self.http.aclose()

    @property
    def methods(self) -> list[str]:
        """Return discovered API method IDs."""
        return sorted(self.discovery.methods)

    @property
    def scopes(self) -> list[str]:
        """Return API-level OAuth scopes."""
        return self.discovery.scopes

    async def call(
        self,
        method_id: str,
        *,
        body: object = None,
        **kwargs: object,
    ) -> object:
        """Execute a discovered Google Health API method."""
        await self.discovery.load()

        method = self.discovery.get(method_id)
        parameters = method.get("parameters", {})

        if not isinstance(parameters, dict):
            message = "Invalid API method parameters"
            raise GoogleHealthError(message)

        path, remaining = resolve_path(
            method["path"],
            parameters,
            kwargs,
        )

        query_values = resolve_query(
            parameters,
            remaining,
        )

        allowed = {
            name for name, definition in parameters.items() if definition.get("location") == "query"
        }

        unknown = set(remaining) - allowed

        if unknown:
            message = f"Unexpected API parameters: {sorted(unknown)}"
            raise TypeError(message)

        document = self.discovery.document

        if document is None:
            message = "Discovery document is not loaded"
            raise GoogleHealthError(message)

        root = document.get(
            "rootUrl",
            "https://health.googleapis.com/",
        )

        service = document.get("servicePath", "")

        if not isinstance(root, str):
            message = "Invalid Discovery rootUrl"
            raise GoogleHealthError(message)

        if not isinstance(service, str):
            message = "Invalid Discovery servicePath"
            raise GoogleHealthError(message)

        url = _build_url(
            root,
            service,
            path,
        )

        return await self.transport.request(
            method["httpMethod"],
            url,
            params=httpx.QueryParams(query_values),
            body=body,
        )
