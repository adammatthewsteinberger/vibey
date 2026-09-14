# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Table-driven OpenAI error-code taxonomy and CodexloopError hierarchy."""

from __future__ import annotations

import pytest

from codexloop.domain.error_codes import (
    AUTH_CODES,
    FATAL_CODES,
    QUOTA_CODES,
    THROTTLE_CODES,
    TRANSIENT_CODES,
    WINDOW_CODES,
    ErrorClass,
    classify_code,
)
from codexloop.domain.errors import (
    AuthError,
    BudgetExceeded,
    CapacityError,
    CodexBinaryError,
    CodexloopError,
    CodexProtocolError,
    ConfigurationError,
    WaitDeadlineExceeded,
)

CODE_TABLE: list[tuple[str, ErrorClass]] = [
    ("insufficient_quota", ErrorClass.QUOTA),
    ("credit_balance_exhausted", ErrorClass.QUOTA),
    ("usage_not_included", ErrorClass.QUOTA),
    ("usage_limit_reached", ErrorClass.WINDOW),
    ("rate_limit_exceeded", ErrorClass.THROTTLE),
    ("slow_down", ErrorClass.THROTTLE),
    ("server_is_overloaded", ErrorClass.TRANSIENT),
    ("invalid_api_key", ErrorClass.AUTH),
    ("token_expired", ErrorClass.AUTH),
    ("refresh_token_expired", ErrorClass.AUTH),
    ("refresh_token_reused", ErrorClass.AUTH),
    ("refresh_token_invalidated", ErrorClass.AUTH),
    ("context_length_exceeded", ErrorClass.FATAL),
    ("invalid_prompt", ErrorClass.FATAL),
]

RETRYABLE_SETS = (WINDOW_CODES, THROTTLE_CODES, TRANSIENT_CODES)


@pytest.mark.parametrize(("code", "expected"), CODE_TABLE)
def test_classify_code_maps_known_codes(code: str, expected: ErrorClass) -> None:
    assert classify_code(code, None) == expected


@pytest.mark.parametrize(("type_", "expected"), CODE_TABLE)
def test_classify_code_consults_type_when_code_absent(type_: str, expected: ErrorClass) -> None:
    assert classify_code(None, type_) == expected


def test_classify_code_unknown_falls_through() -> None:
    assert classify_code("totally_unknown_code", None) == ErrorClass.UNKNOWN
    assert classify_code(None, "totally_unknown_type") == ErrorClass.UNKNOWN
    assert classify_code(None, None) == ErrorClass.UNKNOWN


def test_classify_code_prefers_code_over_type() -> None:
    assert classify_code("insufficient_quota", "usage_limit_reached") == ErrorClass.QUOTA
    assert classify_code("rate_limit_exceeded", "insufficient_quota") == ErrorClass.THROTTLE


def test_quota_and_auth_disjoint_from_every_retryable_set() -> None:
    for non_retryable in (QUOTA_CODES, AUTH_CODES):
        for retryable in RETRYABLE_SETS:
            assert non_retryable.isdisjoint(retryable)


def test_taxonomy_sets_are_frozen() -> None:
    for codes in (
        QUOTA_CODES,
        AUTH_CODES,
        WINDOW_CODES,
        THROTTLE_CODES,
        TRANSIENT_CODES,
        FATAL_CODES,
    ):
        assert isinstance(codes, frozenset)


@pytest.mark.parametrize(
    ("exc_type",),
    [
        (ConfigurationError,),
        (CapacityError,),
        (AuthError,),
        (CodexBinaryError,),
        (CodexProtocolError,),
        (BudgetExceeded,),
        (WaitDeadlineExceeded,),
    ],
)
def test_exception_hierarchy(exc_type: type[CodexloopError]) -> None:
    err = exc_type("boom")
    assert isinstance(err, CodexloopError)
    assert isinstance(err, Exception)
    assert str(err) == "boom"
