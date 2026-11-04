
# Google Health Client

Async Python client for the Google Health API.

## Requirements

- Python 3.14+
- HTTPX
- Google Health API OAuth access token

## Installation

```bash
uv sync --group dev
```

## Usage

```python
import asyncio

from google_health import GoogleHealthClient


async def main() -> None:
    async with GoogleHealthClient(
        access_token="YOUR_ACCESS_TOKEN"
    ) as client:

        # Discover available methods.
        for method in client.methods:
            print(method)

        # Inspect OAuth scopes.
        for scope in client.scopes:
            print(scope)

        # Fetch profile.
        profile = await client.call(
            "health.users.getProfile",
            name="users/me/profile",
        )

        print(profile)


asyncio.run(main())
```

## Run tests

```bash
just test
```

## Lint

```bash
just fixup
```

## Type checking

```bash
just type-check
```

## Google API Discovery

https://health.googleapis.com/$discovery/rest?version=v4

## Google Health API Reference

https://developers.google.com/health/reference/rest
