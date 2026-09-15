# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

import dataclasses
from datetime import UTC, datetime

import pytest

from cursorloop.domain.capacity import (
    AuthenticationFailed,
    Available,
    CreditsExhausted,
    WindowExhausted,
    is_waitable,
)


def test_credits_exhausted_has_no_reset_field_at_all() -> None:
    """THE load-bearing invariant. Not `resets_at=None` — the type must be
    incapable of expressing a reset instant, so no code path can compute a
    deadline from an empty balance and no future contributor can add one
    'for consistency' without deleting this test."""
    fields = {f.name for f in dataclasses.fields(CreditsExhausted)}
    assert "resets_at" not in fields
    assert "reset_at" not in fields
    assert fields == {"can_purchase"}


def test_window_exhausted_carries_optional_reset() -> None:
    at = datetime(2026, 8, 13, 14, 5, tzinfo=UTC)
    assert WindowExhausted("rate_limit", at).resets_at == at
    assert WindowExhausted("rate_limit").resets_at is None


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        (Available(), True),
        (WindowExhausted("rate_limit"), True),
        (CreditsExhausted(), True),
        (AuthenticationFailed("revoked"), False),
    ],
)
def test_only_authentication_failure_is_unwaitable(state: object, expected: bool) -> None:
    assert is_waitable(state) is expected  # type: ignore[arg-type]


def test_states_are_frozen() -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        Available().utilization = 0.5  # type: ignore[misc]
