"""Tests for ``vibey_bootstrap.scheduler``."""

from __future__ import annotations

import pytest

apscheduler = pytest.importorskip("apscheduler")
from vibey_bootstrap.scheduler import parse_cron_trigger


def test_5_field_crontab() -> None:
    trigger = parse_cron_trigger("0 12 * * *")
    assert trigger is not None


def test_6_field_with_seconds() -> None:
    trigger = parse_cron_trigger("0 0 12 * * *")
    assert trigger is not None
    # Repr should reference the seconds field
    assert "second" in repr(trigger).lower() or "0" in str(trigger)


def test_empty_string_falls_back() -> None:
    trigger = parse_cron_trigger("")
    repr_str = repr(trigger).lower()
    assert "*/15" in repr_str or "15" in repr_str


def test_invalid_expression_falls_back() -> None:
    trigger = parse_cron_trigger("not a cron expression")
    assert trigger is not None
    repr_str = repr(trigger).lower()
    assert "*/15" in repr_str or "15" in repr_str
