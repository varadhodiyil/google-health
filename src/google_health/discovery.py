"""Discovery module."""

import logging
from typing import TypedDict

import httpx

from .exceptions import DiscoveryError, MethodNotFoundError

logger = logging.getLogger(__name__)
DISCOVERY_URL = "https://health.googleapis.com/$discovery/rest?version=v4"


class DiscoveryMethod(TypedDict, total=False):
    """Google API method definition."""

    id: str
    path: str
    httpMethod: str
    parameters: dict[str, dict[str, object]]
    request: dict[str, str]
    response: dict[str, str]
    scopes: list[str]


class Discovery:
    """Load and index Google API Discovery metadata."""

    def __init__(
        self,
        http: httpx.AsyncClient,
        url: str = DISCOVERY_URL,
    ) -> None:
        self.http = http
        self.url = url
        self.document: dict[str, object] | None = None
        self.methods: dict[str, DiscoveryMethod] = {}

    async def load(self) -> None:
        """Download and cache the Discovery Document."""
        if self.document is not None:
            return

        try:
            response = await self.http.get(self.url)
            response.raise_for_status()
            document = response.json()

        except httpx.HTTPError as exc:
            logger.exception("Failed to load discovery document")
            message = "Failed to download API discovery document"
            raise DiscoveryError(message) from exc

        except ValueError as exc:
            message = "Invalid API discovery JSON"
            raise DiscoveryError(message) from exc

        if not isinstance(document, dict):
            message = "Discovery document must be a JSON object"
            raise DiscoveryError(message)

        resources = document.get("resources", {})

        if not isinstance(resources, dict):
            message = "Invalid Discovery resources"
            raise DiscoveryError(message)

        self.document = document
        self._index(resources)

    def _index(self, resources: dict[str, object]) -> None:
        """Recursively index API methods."""
        for resource in resources.values():
            if not isinstance(resource, dict):
                continue

            methods = resource.get("methods", {})

            if isinstance(methods, dict):
                for method in methods.values():
                    if not isinstance(method, dict):
                        continue

                    method_id = method.get("id")

                    if isinstance(method_id, str):
                        self.methods[method_id] = method

            nested = resource.get("resources", {})

            if isinstance(nested, dict):
                self._index(nested)

    def get(self, method_id: str) -> DiscoveryMethod:
        """Return a method definition."""
        try:
            return self.methods[method_id]

        except KeyError:
            raise MethodNotFoundError(method_id) from None

    @property
    def scopes(self) -> list[str]:
        """Return API-level OAuth scopes."""
        if self.document is None:
            return []

        auth = self.document.get("auth")

        if not isinstance(auth, dict):
            return []

        oauth = auth.get("oauth2")

        if not isinstance(oauth, dict):
            return []

        scopes = oauth.get("scopes")

        if not isinstance(scopes, dict):
            return []

        return sorted(scopes)
