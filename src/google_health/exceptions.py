"""Base exceptions."""


class GoogleHealthError(Exception):
    """Base exception for Google Health."""


class DiscoveryError(GoogleHealthError):
    """Raised when the API discovery document cannot be loaded."""


class MethodNotFoundError(GoogleHealthError):
    """Raised when an API method cannot be found."""

    def __init__(self, method_id: str) -> None:
        message = f"Unknown Google Health API method: {method_id}"
        super().__init__(message)


class MissingParameterError(GoogleHealthError):
    """Raised when a required API parameter is missing."""

    def __init__(self, parameter: str) -> None:
        message = f"Missing required API parameter: {parameter}"
        super().__init__(message)


class AuthenticationError(GoogleHealthError):
    """Raised when authentication or authorization fails."""


class APIError(GoogleHealthError):
    """Raised when Google returns an unsuccessful API response."""

    def __init__(
        self,
        status_code: int,
        details: object,
    ) -> None:
        self.status_code = status_code
        self.details = details

        message = f"Google Health returned HTTP {status_code}"
        super().__init__(message)
