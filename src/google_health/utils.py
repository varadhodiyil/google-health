"""Google Discovery URL template utilities."""

import re
from typing import Any
from urllib.parse import quote

from uritemplate import URITemplate

from .exceptions import MissingParameterError

type ParameterDefinition = dict[str, object]
type Parameters = dict[str, ParameterDefinition]
type ParameterValues = dict[str, Any]


GOOGLE_TEMPLATE_PATTERN = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)=([^{}]*)\}")


def resolve_path(
    path: str,
    parameters: Parameters,
    values: ParameterValues,
) -> tuple[str, ParameterValues]:
    """Expand Google Discovery URI templates."""
    remaining = values.copy()

    path_parameters = {
        name: definition
        for name, definition in parameters.items()
        if definition.get("location") == "path"
    }

    for name, definition in path_parameters.items():
        if name not in remaining and definition.get("required") is True:
            raise MissingParameterError(name)

    google_templates = GOOGLE_TEMPLATE_PATTERN.findall(path)

    for name, _ in google_templates:
        if name not in remaining:
            continue

        replacement = quote(str(remaining.pop(name)), safe="/")

        path = re.sub(
            r"\{" + re.escape(name) + r"=[^{}]*\}",
            lambda _, value=replacement: value,
            path,
        )

    template_variables = URITemplate(path).variable_names

    template_values = {name: remaining[name] for name in template_variables if name in remaining}

    expanded = URITemplate(path).expand(template_values)

    for name in template_values:
        remaining.pop(name)

    return expanded, remaining


def resolve_query(
    parameters: Parameters,
    values: ParameterValues,
) -> ParameterValues:
    """Resolve Google API query parameters."""
    query: ParameterValues = {}

    for name, definition in parameters.items():
        if definition.get("location") != "query":
            continue

        if name in values:
            query[name] = values[name]

        elif definition.get("required") is True:
            raise MissingParameterError(name)

    return query
