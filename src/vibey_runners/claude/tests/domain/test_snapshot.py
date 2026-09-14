# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Domain tests for snapshot ADTs and digests."""

from __future__ import annotations

import pytest

from claudeloop.domain.snapshot import (
    BUNDLE_REASONS,
    IMMUTABLE_REASONS,
    SNAPSHOT_SCHEMA_VERSION,
    digest_payload,
    parse_snapshot_reason,
)


def test_schema_version_is_positive() -> None:
    assert SNAPSHOT_SCHEMA_VERSION >= 1


def test_digest_is_stable_for_key_order() -> None:
    a = digest_payload({"b": 1, "a": 2})
    b = digest_payload({"a": 2, "b": 1})
    assert a == b
    assert len(a) == 64


def test_digest_changes_when_value_changes() -> None:
    assert digest_payload({"x": 1}) != digest_payload({"x": 2})


def test_parse_snapshot_reason() -> None:
    assert parse_snapshot_reason(" Started ") == "started"
    with pytest.raises(ValueError, match="invalid snapshot reason"):
        parse_snapshot_reason("nope")


def test_reason_sets() -> None:
    assert "status" not in IMMUTABLE_REASONS
    assert "manual" in BUNDLE_REASONS
    assert "started" not in BUNDLE_REASONS
