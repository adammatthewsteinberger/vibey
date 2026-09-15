# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Lightweight JSON / queue-message schema validation.

Designed for the narrow case of validating untrusted queue payloads cheaply
at the consumer entry point — not a pydantic replacement. Schema failures
raise :class:`InvalidMessageError` (unrecoverable per the v2 exception
contract) so the Service Bus consumer wrapper dead-letters them.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from vibey_bootstrap.counters import bump_counter
from vibey_bootstrap.exceptions import InvalidMessageError

_logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FieldRule:
    name: str
    required: bool = True
    type: type | tuple[type, ...] = str
    non_empty: bool = True
    pattern: str | None = None
    forbidden_substrings: tuple[str, ...] = ()
    forbidden_prefixes: tuple[str, ...] = ()
    required_prefix: str | None = None


@dataclass(frozen=True)
class MessageSchema:
    fields: tuple[FieldRule, ...]
    counter_namespace: str = "queue_message"


def _bump_rejection(schema: MessageSchema) -> None:
    bump_counter(f"{schema.counter_namespace}.rejected.schema")


def _check_field(rule: FieldRule, payload: dict[str, Any]) -> str | None:
    """Return None on pass, an error string on fail."""
    value = payload.get(rule.name)
    if value is None or (isinstance(value, str) and not value):
        if rule.required:
            return f"missing required field {rule.name!r}"
        return None

    if not isinstance(value, rule.type):
        return (
            f"field {rule.name!r} has wrong type (expected {rule.type}, got {type(value).__name__})"
        )

    if isinstance(value, str):
        if rule.non_empty and not value.strip():
            return f"field {rule.name!r} is empty"
        if rule.pattern is not None and not re.search(rule.pattern, value):
            return f"field {rule.name!r} does not match pattern {rule.pattern!r}"
        for forbidden in rule.forbidden_substrings:
            if forbidden in value:
                return f"field {rule.name!r} contains forbidden substring {forbidden!r}"
        for prefix in rule.forbidden_prefixes:
            if value.startswith(prefix):
                return f"field {rule.name!r} starts with forbidden prefix {prefix!r}"
        if rule.required_prefix is not None and not value.startswith(rule.required_prefix):
            return f"field {rule.name!r} must start with {rule.required_prefix!r}"
    return None


def validate_message(
    payload: Any,
    schema: MessageSchema,
    *,
    raise_unrecoverable: bool = True,
) -> dict[str, Any]:
    """Validate ``payload`` against ``schema``. Returns the dict on success.

    Failures (non-dict, missing field, type mismatch, pattern, forbidden
    substring/prefix, required_prefix) bump the namespaced counter and
    raise :class:`InvalidMessageError` by default.
    """
    if not isinstance(payload, dict):
        _bump_rejection(schema)
        if raise_unrecoverable:
            raise InvalidMessageError(
                f"payload is not a JSON object (got {type(payload).__name__})"
            )
        return {}

    for rule in schema.fields:
        reason = _check_field(rule, payload)
        if reason:
            _bump_rejection(schema)
            _logger.warning(
                "validate_message: rejected — %s",
                reason,
                extra={
                    "operation": "validate_message",
                    "schema_namespace": schema.counter_namespace,
                    "reason": reason,
                },
            )
            if raise_unrecoverable:
                raise InvalidMessageError(reason)
            return {}

    return payload


def queue_message_schema(
    *,
    required_fields: Iterable[str] = ("correlation_id",),
    path_field: str | None = None,
    path_required_prefix: str | None = None,
    counter_namespace: str = "queue_message",
) -> MessageSchema:
    """Build a sensible MessageSchema for the common consumer case.

    Adds path-traversal defense (forbidden substrings ``..`` and ``://``)
    when ``path_field`` is supplied. ``required_prefix`` enforces a blob /
    container scoping convention.
    """
    rules: list[FieldRule] = [
        FieldRule(name=name, required=True, type=str, non_empty=True) for name in required_fields
    ]
    if path_field is not None:
        rules.append(
            FieldRule(
                name=path_field,
                required=True,
                type=str,
                non_empty=True,
                forbidden_substrings=("..", "://"),
                required_prefix=path_required_prefix,
            )
        )
    return MessageSchema(fields=tuple(rules), counter_namespace=counter_namespace)


__all__ = [
    "FieldRule",
    "InvalidMessageError",
    "MessageSchema",
    "queue_message_schema",
    "validate_message",
]
