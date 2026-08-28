# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
from datetime import UTC, datetime

from vibey.domain.capacity import (
    AuthenticationFailed,
    Available,
    CreditsExhausted,
    WindowExhausted,
)


def test_available_constructs() -> None:
    Available()


def test_window_exhausted_defaults() -> None:
    state = WindowExhausted()
    assert state.resets_at is None
    assert state.rate_limit_type is None


def test_window_exhausted_with_deadline() -> None:
    dt = datetime(2026, 1, 1, tzinfo=UTC)
    state = WindowExhausted(resets_at=dt, rate_limit_type="rpm")
    assert state.resets_at == dt


def test_credits_exhausted_has_no_resets_at_field() -> None:
    state = CreditsExhausted()
    assert not hasattr(state, "resets_at")
    assert "resets_at" not in CreditsExhausted.__slots__


def test_credits_exhausted_can_purchase_default() -> None:
    assert CreditsExhausted().can_purchase is True
    assert CreditsExhausted(can_purchase=False).can_purchase is False


def test_authentication_failed_carries_detail() -> None:
    state = AuthenticationFailed(detail="expired token")
    assert state.detail == "expired token"
