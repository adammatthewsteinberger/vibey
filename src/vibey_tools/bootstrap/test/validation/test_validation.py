"""Tests for ``vibey_bootstrap.validation``."""

from __future__ import annotations

import pytest

from vibey_bootstrap.counters import _reset_counters, counter_snapshot
from vibey_bootstrap.exceptions import InvalidMessageError
from vibey_bootstrap.validation import (
    FieldRule,
    MessageSchema,
    queue_message_schema,
    validate_message,
)


@pytest.fixture(autouse=True)
def _reset() -> None:
    _reset_counters()


def test_rejects_non_dict() -> None:
    schema = MessageSchema(fields=(FieldRule(name="x"),))
    with pytest.raises(InvalidMessageError):
        validate_message(["not", "a", "dict"], schema)


def test_rejects_missing_required() -> None:
    schema = MessageSchema(fields=(FieldRule(name="correlation_id"),))
    with pytest.raises(InvalidMessageError, match="missing required"):
        validate_message({}, schema)


def test_rejects_path_traversal() -> None:
    schema = queue_message_schema(
        required_fields=("correlation_id",),
        path_field="blob_path",
    )
    with pytest.raises(InvalidMessageError, match=r"forbidden substring '\.\.'"):
        validate_message(
            {"correlation_id": "x", "blob_path": "good/../etc/passwd"},
            schema,
        )


def test_rejects_url_scheme() -> None:
    schema = queue_message_schema(
        required_fields=("correlation_id",),
        path_field="blob_path",
    )
    with pytest.raises(InvalidMessageError, match=r"forbidden substring '://'"):
        validate_message(
            {"correlation_id": "x", "blob_path": "https://evil/etc"},
            schema,
        )


def test_enforces_prefix() -> None:
    schema = queue_message_schema(
        required_fields=("correlation_id",),
        path_field="blob_path",
        path_required_prefix="reports/",
    )
    with pytest.raises(InvalidMessageError, match="must start with 'reports/'"):
        validate_message(
            {"correlation_id": "x", "blob_path": "other/x.pdf"},
            schema,
        )


def test_accepts_valid() -> None:
    schema = queue_message_schema(
        required_fields=("correlation_id",),
        path_field="blob_path",
        path_required_prefix="reports/",
    )
    out = validate_message(
        {"correlation_id": "abc", "blob_path": "reports/x.pdf"},
        schema,
    )
    assert out["correlation_id"] == "abc"


def test_bumps_counter_on_rejection() -> None:
    schema = MessageSchema(
        fields=(FieldRule(name="x"),),
        counter_namespace="my_queue",
    )
    with pytest.raises(InvalidMessageError):
        validate_message({}, schema)
    assert counter_snapshot().get("my_queue.rejected.schema", 0) == 1


def test_non_raising_mode_returns_empty_dict() -> None:
    schema = MessageSchema(fields=(FieldRule(name="x"),))
    out = validate_message({}, schema, raise_unrecoverable=False)
    assert out == {}


def test_type_check() -> None:
    schema = MessageSchema(fields=(FieldRule(name="n", type=int),))
    with pytest.raises(InvalidMessageError, match="wrong type"):
        validate_message({"n": "not-an-int"}, schema)
