
"""Tests for API URL and parameter utilities."""

import pytest

from google_health.exceptions import MissingParameterError
from google_health.utils import resolve_path, resolve_query


@pytest.mark.parametrize(
    ("path", "value", "expected"),
    [
        (
            "v4/{name=users/*/profile}",
            "users/me/profile",
            "v4/users/me/profile",
        ),
        (
            "v4/{parent=users/*/dataTypes/*}/dataPoints",
            "users/me/dataTypes/steps",
            "v4/users/me/dataTypes/steps/dataPoints",
        ),
    ],
)
def test_resolve_path(
    path: str,
    value: str,
    expected: str,
) -> None:
    """Test Google API path template resolution."""
    result, remaining = resolve_path(
        path,
        {
            "name" if "name=" in path else "parent": {
                "location": "path",
                "required": True,
            },
        },
        {
            "name" if "name=" in path else "parent": value,
        },
    )

    assert result == expected
    assert remaining == {}


def test_missing_path_parameter() -> None:
    """Test missing required path parameters."""
    with pytest.raises(MissingParameterError):
        resolve_path(
            "v4/{name=users/*/profile}",
            {
                "name": {
                    "location": "path",
                    "required": True,
                },
            },
            {},
        )


def test_resolve_query() -> None:
    """Test query parameter resolution."""
    result = resolve_query(
        {
            "pageSize": {
                "location": "query",
                "type": "integer",
            },
        },
        {"pageSize": 100},
    )

    assert result == {"pageSize": 100}



def test_reserved_expansion() -> None:
    """Test RFC 6570 reserved expansion."""
    result, remaining = resolve_path(
        "v4/{+name}",
        {
            "name": {
                "location": "path",
                "required": True,
            },
        },
        {
            "name": "users/me/profile",
        },
    )

    assert result == "v4/users/me/profile"
    assert remaining == {}
