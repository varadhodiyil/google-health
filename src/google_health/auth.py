"""OAuth bearer-token authentication."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydantic import SecretStr


@dataclass(slots=True)
class BearerAuth:
    """Manage Google OAuth bearer tokens."""

    access_token: SecretStr

    def __post_init__(self) -> None:
        """Validate token."""
        if not self.access_token.get_secret_value().strip():
            message = "Access token cannot be empty"
            raise ValueError(message)

    def headers(self) -> dict[str, str]:
        """Return authentication headers."""
        return {
            "Authorization": ("Bearer " + self.access_token.get_secret_value()),
            "Accept": "application/json",
        }

    def update_token(self, access_token: SecretStr) -> None:
        """Update the access token."""
        if not access_token.get_secret_value().strip():
            message = "Access token cannot be empty"
            raise ValueError(message)

        self.access_token = access_token
