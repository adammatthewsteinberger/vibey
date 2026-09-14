# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from hypothesis import given
from hypothesis import strategies as st

from cursorloop.domain.retry_after import parse_retry_after

NOW = datetime(2026, 8, 13, 12, 0, 0, tzinfo=UTC)


def test_integer_seconds_form() -> None:
    assert parse_retry_after("120", now=NOW) == NOW + timedelta(seconds=120)


def test_float_seconds_form_is_tolerated() -> None:
    assert parse_retry_after("1.5", now=NOW) == NOW + timedelta(seconds=1.5)


def test_http_date_form() -> None:
    assert parse_retry_after("Wed, 13 Aug 2026 14:05:00 GMT", now=NOW) == datetime(
        2026, 8, 13, 14, 5, 0, tzinfo=UTC
    )


def test_http_date_without_timezone_uses_now_tzinfo() -> None:
    assert parse_retry_after("13 Aug 2026 14:05:00", now=NOW) == datetime(
        2026, 8, 13, 14, 5, 0, tzinfo=UTC
    )


def test_none_and_blank_are_absent_not_errors() -> None:
    assert parse_retry_after(None, now=NOW) is None
    assert parse_retry_after("   ", now=NOW) is None


def test_negative_seconds_clamp_to_now() -> None:
    """A server clock skew must never produce an instant in the past — the
    wait policy would then busy-spin."""
    assert parse_retry_after("-30", now=NOW) == NOW


def test_past_http_date_clamps_to_now() -> None:
    assert parse_retry_after("Wed, 13 Aug 2026 10:00:00 GMT", now=NOW) == NOW


def test_unparseable_value_returns_none() -> None:
    assert parse_retry_after("not-a-date-or-seconds", now=NOW) is None


def test_nan_seconds_returns_none_not_raises() -> None:
    assert parse_retry_after("nan", now=NOW) is None


def test_overflow_seconds_returns_none_not_raises() -> None:
    assert parse_retry_after("1e300", now=NOW) is None


def test_http_date_with_naive_now_never_raises() -> None:
    naive_now = datetime(2026, 8, 13, 12, 0, 0)
    assert parse_retry_after("Wed, 13 Aug 2026 14:05:00 GMT", now=naive_now) is None


@given(st.text())
def test_never_raises_on_arbitrary_input(value: str) -> None:
    """A multi-hour unattended run must not die on a malformed header."""
    result = parse_retry_after(value, now=NOW)
    assert result is None or result >= NOW
