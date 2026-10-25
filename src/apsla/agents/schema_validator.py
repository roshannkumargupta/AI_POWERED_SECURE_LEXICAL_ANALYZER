"""Neutral JSON Schema validator for agent tool arguments and structured outputs."""

from __future__ import annotations

from typing import Any


def validate_schema(data: Any, schema: dict[str, Any]) -> bool:
    """Hermetic schema validator without external dependencies."""
    if not isinstance(schema, dict):
        return True

    expected_type = schema.get("type")
    if expected_type == "object":
        if not isinstance(data, dict):
            return False
        # Required properties
        for req in schema.get("required", []):
            if req not in data:
                return False
        # Validate properties
        props = schema.get("properties", {})
        return all(not (k in props and not validate_schema(v, props[k])) for k, v in data.items())

    if expected_type == "array":
        if not isinstance(data, list):
            return False
        item_schema = schema.get("items")
        if item_schema and isinstance(item_schema, dict):
            for item in data:
                if not validate_schema(item, item_schema):
                    return False
        return True

    if expected_type == "string":
        if not isinstance(data, str):
            return False
        return not ("enum" in schema and data not in schema["enum"])

    if expected_type == "integer":
        if not isinstance(data, int) or isinstance(data, bool):
            return False
        return not ("enum" in schema and data not in schema["enum"])

    if expected_type == "number":
        return not (not isinstance(data, (int, float)) or isinstance(data, bool))

    if expected_type == "boolean":
        return isinstance(data, bool)

    return not ("enum" in schema and data not in schema["enum"])
