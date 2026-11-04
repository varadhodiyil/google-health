"""Daily activity aggregation helpers."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date

    from google_health.client import GoogleHealthClient


def _civil_time(value: date) -> dict[str, object]:
    return {
        "date": {
            "year": value.year,
            "month": value.month,
            "day": value.day,
        },
        "time": {},
    }


async def daily_summary(
    client: GoogleHealthClient,
    *,
    data_type: str,
    start_date: date,
    end_date: date,
) -> object:
    """
    Retrieve daily aggregated health data.

    The end date is exclusive.
    """
    if start_date >= end_date:
        message = "End date must be after start date"
        raise ValueError(message)

    return await client.call(
        "health.users.dataTypes.dataPoints.dailyRollUp",
        parent=f"users/me/dataTypes/{data_type}",
        body={
            "range": {
                "start": _civil_time(start_date),
                "end": _civil_time(end_date),
            },
            "windowSizeDays": 1,
        },
    )


async def daily_steps(
    client: GoogleHealthClient,
    start_date: date,
    end_date: date,
) -> object:
    """Retrieve daily step summaries."""
    return await daily_summary(
        client,
        data_type="steps",
        start_date=start_date,
        end_date=end_date,
    )


async def daily_distance(
    client: GoogleHealthClient,
    start_date: date,
    end_date: date,
) -> object:
    """Retrieve daily distance summaries."""
    return await daily_summary(
        client,
        data_type="distance",
        start_date=start_date,
        end_date=end_date,
    )
