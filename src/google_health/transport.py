"""Transport client."""

from typing import TYPE_CHECKING

from .exceptions import APIError, AuthenticationError

if TYPE_CHECKING:
    import httpx

    from .auth import BearerAuth


class Transport:
    """Execute authenticated HTTP requests."""

    def __init__(
        self,
        auth: BearerAuth,
        http: httpx.AsyncClient,
    ) -> None:
        self.auth = auth
        self.http = http

    async def request(
        self,
        method: str,
        url: str,
        *,
        params: httpx.QueryParams | None = None,
        body: object = None,
    ) -> object:
        """Execute an HTTP request."""
        response = await self.http.request(
            method,
            url,
            params=params,
            json=body,
            headers=self.auth.headers(),
        )

        if response.status_code in (401, 403):
            msg = "Google Health authentication failed"
            raise AuthenticationError(msg)

        if response.is_error:
            try:
                details: object = response.json()
            except ValueError:
                details = response.text

            raise APIError(
                response.status_code,
                details,
            )

        if not response.content:
            return None

        if "json" in response.headers.get("content-type", ""):
            return response.json()

        return response.content
