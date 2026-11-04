"""Main Runner."""

import asyncio
from datetime import date
from logging import getLogger

from activities import daily_distance, daily_steps
from google_health import GoogleHealthClient
from google_health.config import Settings

logger = getLogger(__name__)


async def main() -> None:
    settings = Settings()

    async with GoogleHealthClient(settings) as client:
        profile = await client.call(
            "health.users.getProfile",
            name="users/me/profile",
        )
        logger.info(profile)

        steps = await daily_steps(
            client,
            date(2026, 11, 1),
            date(2026, 11, 4),
        )

        distance = await daily_distance(
            client,
            date(2026, 11, 1),
            date(2026, 11, 4),
        )

        logger.info("Steps: %s", steps)
        logger.info("Distance: %s", distance)


if __name__ == "__main__":
    asyncio.run(main())
