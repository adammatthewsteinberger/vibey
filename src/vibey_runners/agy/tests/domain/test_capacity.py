# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from agyloop.domain.capacity import (
    AuthenticationFailed,
    Available,
    CreditsExhausted,
    TransientThrottle,
    WindowExhausted,
    is_waitable,
)


def test_credits_exhausted_structurally_omits_resets_at() -> None:
    assert "resets_at" not in CreditsExhausted.__dataclass_fields__


def test_available_is_waitable() -> None:
    assert is_waitable(Available()) is True


def test_transient_throttle_is_waitable() -> None:
    assert is_waitable(TransientThrottle()) is True


def test_window_exhausted_is_waitable() -> None:
    assert is_waitable(WindowExhausted(rate_limit_type="rpm")) is True


def test_credits_exhausted_is_waitable() -> None:
    assert is_waitable(CreditsExhausted()) is True


def test_authentication_failed_is_not_waitable() -> None:
    assert is_waitable(AuthenticationFailed()) is False
