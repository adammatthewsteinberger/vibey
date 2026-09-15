# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""OpenAI / Codex error-code taxonomy for capacity classification."""

from __future__ import annotations

from enum import Enum, auto


class ErrorClass(Enum):
    """Coarse classification of vendor error codes / types."""

    AUTH = auto()
    QUOTA = auto()
    WINDOW = auto()
    THROTTLE = auto()
    TRANSIENT = auto()
    FATAL = auto()
    UNKNOWN = auto()


QUOTA_CODES: frozenset[str] = frozenset(
    {
        "insufficient_quota",
        "credit_balance_exhausted",
        "usage_not_included",
    }
)

AUTH_CODES: frozenset[str] = frozenset(
    {
        "invalid_api_key",
        "token_expired",
        "refresh_token_expired",
        "refresh_token_reused",
        "refresh_token_invalidated",
    }
)

WINDOW_CODES: frozenset[str] = frozenset({"usage_limit_reached"})

THROTTLE_CODES: frozenset[str] = frozenset(
    {
        "rate_limit_exceeded",
        "slow_down",
    }
)

TRANSIENT_CODES: frozenset[str] = frozenset({"server_is_overloaded"})

FATAL_CODES: frozenset[str] = frozenset(
    {
        "context_length_exceeded",
        "invalid_prompt",
    }
)

_CODE_TO_CLASS: dict[str, ErrorClass] = {
    **dict.fromkeys(QUOTA_CODES, ErrorClass.QUOTA),
    **dict.fromkeys(AUTH_CODES, ErrorClass.AUTH),
    **dict.fromkeys(WINDOW_CODES, ErrorClass.WINDOW),
    **dict.fromkeys(THROTTLE_CODES, ErrorClass.THROTTLE),
    **dict.fromkeys(TRANSIENT_CODES, ErrorClass.TRANSIENT),
    **dict.fromkeys(FATAL_CODES, ErrorClass.FATAL),
}


def classify_code(code: str | None, type_: str | None) -> ErrorClass:
    """Map an OpenAI/Codex ``error.code`` / ``error.type`` to an :class:`ErrorClass`.

    Prefers ``code`` when present; consults ``type_`` only when ``code`` is absent.
    Unrecognised values yield :attr:`ErrorClass.UNKNOWN`.
    """
    token = code if code is not None else type_
    if token is None:
        return ErrorClass.UNKNOWN
    return _CODE_TO_CLASS.get(token, ErrorClass.UNKNOWN)
