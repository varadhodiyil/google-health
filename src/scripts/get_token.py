"""Google Health OAuth2 authorization script."""

import asyncio
import json
import logging
import secrets
import threading
import webbrowser
from base64 import urlsafe_b64encode
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlsplit

import httpx

from google_health.config import Settings
from google_health.discovery import Discovery

logger = logging.getLogger(__name__)

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"  # noqa: S105


class OAuthCallbackServer(HTTPServer):
    """Local HTTP server receiving the OAuth callback."""

    def __init__(
        self,
        address: tuple[str, int],
        state: str,
        callback_path: str,
    ) -> None:
        self.state = state
        self.callback_path = callback_path
        self.authorization_code: str | None = None
        self.oauth_error: str | None = None

        super().__init__(address, self._handler())

    def _handler(self) -> type[BaseHTTPRequestHandler]:
        """Create the OAuth callback handler."""
        server = self

        class Handler(BaseHTTPRequestHandler):
            """Handle OAuth redirects."""

            def do_GET(self) -> None:
                """Process the authorization response."""
                parsed = urlsplit(self.path)
                query = parse_qs(parsed.query)

                if parsed.path != server.callback_path:
                    self.send_error(404)
                    return

                received_state = query.get("state", [""])[0]

                if not secrets.compare_digest(
                    received_state,
                    server.state,
                ):
                    server.oauth_error = "Invalid OAuth state"
                    self.send_error(400)

                    threading.Thread(
                        target=server.shutdown,
                        daemon=True,
                    ).start()
                    return

                error = query.get("error", [None])[0]

                if error:
                    server.oauth_error = error
                    message = f"Authorization failed: {error}"
                else:
                    server.authorization_code = query.get(
                        "code",
                        [None],
                    )[0]

                    message = "Authorization successful. You can close this browser window."

                self.send_response(200)
                self.send_header(
                    "Content-Type",
                    "text/plain; charset=utf-8",
                )
                self.end_headers()
                self.wfile.write(message.encode("utf-8"))

                threading.Thread(
                    target=server.shutdown,
                    daemon=True,
                ).start()

        return Handler


def create_pkce_pair() -> tuple[str, str]:
    """Generate PKCE verifier and S256 challenge."""
    verifier = secrets.token_urlsafe(64)

    challenge = (
        urlsafe_b64encode(
            sha256(verifier.encode("ascii")).digest(),
        )
        .decode("ascii")
        .rstrip("=")
    )

    return verifier, challenge


async def get_scopes(settings: Settings) -> list[str]:
    """Retrieve supported OAuth scopes from Discovery."""
    async with httpx.AsyncClient(
        timeout=settings.timeout,
    ) as http:
        discovery = Discovery(http)
        await discovery.load()

        scopes = discovery.scopes

    if not scopes:
        message = "No OAuth scopes found in Discovery document"
        raise RuntimeError(message)

    return scopes


def save_tokens(
    settings: Settings,
    tokens: dict[str, object],
) -> None:
    """Persist OAuth tokens to the configured token file."""
    token_file = settings.token_file

    token_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    token_file.write_text(
        json.dumps(tokens, indent=2) + "\n",
        encoding="utf-8",
    )

    token_file.chmod(0o600)

    logger.info("OAuth tokens saved to %s", token_file)


def validate_settings(settings: Settings) -> None:
    """Validate OAuth configuration."""
    redirect = urlsplit(settings.redirect_uri)

    if redirect.scheme != "http":
        message = "OAuth redirect URI must use HTTP"
        raise ValueError(message)

    if redirect.hostname != "127.0.0.1":
        message = "OAuth redirect URI must use 127.0.0.1"
        raise ValueError(message)

    if redirect.username or redirect.password:
        message = "OAuth redirect URI cannot contain credentials"
        raise ValueError(message)

    if redirect.query or redirect.fragment:
        message = "OAuth redirect URI cannot contain query or fragment"
        raise ValueError(message)

    if not redirect.path:
        message = "OAuth redirect URI must include a callback path"
        raise ValueError(message)

    if not settings.client_id.strip():
        message = "OAuth client ID is required"
        raise ValueError(message)

    if not settings.client_secret.get_secret_value().strip():
        message = "OAuth client secret is required"
        raise ValueError(message)


def create_authorization_url(
    settings: Settings,
    scopes: list[str],
    state: str,
    challenge: str,
) -> str:
    """Build the Google authorization URL."""
    params = {
        "client_id": settings.client_id,
        "redirect_uri": settings.redirect_uri,
        "response_type": "code",
        "scope": " ".join(scopes),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }

    return f"{AUTH_URL}?{urlencode(params)}"


def receive_authorization_code(
    settings: Settings,
    authorization_url: str,
    state: str,
) -> str:
    """Open browser and wait for authorization callback."""
    redirect = urlsplit(settings.redirect_uri)

    with OAuthCallbackServer(
        ("127.0.0.1", redirect.port or 80),
        state,
        redirect.path,
    ) as server:
        logger.info("Opening Google authorization page")

        if not webbrowser.open(authorization_url):
            logger.info("Open this URL manually: %s", authorization_url)

        logger.info("Waiting for OAuth callback")

        server.serve_forever()

        if server.oauth_error:
            message = f"OAuth authorization failed: {server.oauth_error}"
            raise RuntimeError(message)

        code = server.authorization_code

    if not code:
        message = "No authorization code received"
        raise RuntimeError(message)

    return code


def exchange_authorization_code(
    settings: Settings,
    code: str,
    verifier: str,
) -> dict[str, object]:
    """Exchange authorization code for OAuth tokens."""
    token_data = {
        "code": code,
        "client_id": settings.client_id,
        "client_secret": settings.client_secret.get_secret_value(),
        "redirect_uri": settings.redirect_uri,
        "grant_type": "authorization_code",
        "code_verifier": verifier,
    }

    with httpx.Client(timeout=settings.timeout) as client:
        response = client.post(
            TOKEN_URL,
            data=token_data,
            headers={"Accept": "application/json"},
        )

        response.raise_for_status()
        tokens = response.json()

    if not isinstance(tokens, dict) or "access_token" not in tokens:
        message = "Invalid OAuth token response"
        raise RuntimeError(message)

    return tokens


def do_login(settings: Settings) -> None:
    """Execute Google OAuth authorization flow."""
    validate_settings(settings)

    scopes = asyncio.run(get_scopes(settings))
    logger.info("Discovered %d OAuth scopes", len(scopes))

    verifier, challenge = create_pkce_pair()
    state = secrets.token_urlsafe(32)

    authorization_url = create_authorization_url(
        settings,
        scopes,
        state,
        challenge,
    )

    code = receive_authorization_code(
        settings,
        authorization_url,
        state,
    )

    tokens = exchange_authorization_code(
        settings,
        code,
        verifier,
    )

    save_tokens(settings, tokens)

    logger.info("OAuth authorization completed")

    if "refresh_token" not in tokens:
        logger.warning("No refresh token returned by Google")

    logger.info(
        "Access token expires in %s seconds",
        tokens.get("expires_in", "unknown"),
    )


def main() -> None:
    """Run OAuth authorization."""
    logging.basicConfig(
        level=logging.INFO,
        format=("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"),
    )

    settings = Settings()

    logger.info(
        "OAuth client ID: %r",
        settings.client_id,
    )

    logger.info(
        "OAuth redirect URI: %r",
        settings.redirect_uri,
    )
    do_login(settings)


if __name__ == "__main__":
    main()
