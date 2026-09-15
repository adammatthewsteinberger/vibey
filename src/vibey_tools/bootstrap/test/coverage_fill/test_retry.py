# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Tests for the retry presets — pure logic, no SDK, and previously untested."""

from __future__ import annotations

import pytest

from vibey_bootstrap.exceptions import NetworkError, RateLimitError
from vibey_bootstrap.retry import (
    _is_rate_limit_or_http,
    build_retry,
    retry_ai_transient,
    retry_azure_transient,
)


class FakeHttpError(Exception):
    def __init__(self, status_code: int) -> None:
        super().__init__(f"http {status_code}")
        self.status_code = status_code


@pytest.mark.parametrize(
    "exc,expected",
    [
        (RateLimitError("slow down"), True),
        (FakeHttpError(429), True),
        (FakeHttpError(503), True),
        (ValueError("nope"), False),
    ],
)
def test_rate_limit_or_http_detection(exc, expected):
    assert _is_rate_limit_or_http(exc) is expected


def test_retries_until_it_succeeds():
    calls = {"n": 0}

    @build_retry(
        operation="op", retry_on=ValueError, max_attempts=4, wait_min_seconds=0, wait_max_seconds=0
    )
    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise ValueError("not yet")
        return "ok"

    assert flaky() == "ok"
    assert calls["n"] == 3


def test_gives_up_after_max_attempts_and_reraises():
    calls = {"n": 0}

    @build_retry(
        operation="op", retry_on=ValueError, max_attempts=2, wait_min_seconds=0, wait_max_seconds=0
    )
    def always_fails():
        calls["n"] += 1
        raise ValueError("always")

    with pytest.raises(ValueError):
        always_fails()
    assert calls["n"] == 2


def test_an_unlisted_exception_is_not_retried():
    calls = {"n": 0}

    @build_retry(
        operation="op", retry_on=ValueError, max_attempts=5, wait_min_seconds=0, wait_max_seconds=0
    )
    def wrong_error():
        calls["n"] += 1
        raise KeyError("different")

    with pytest.raises(KeyError):
        wrong_error()
    assert calls["n"] == 1, "a non-matching exception must not be retried"


def test_a_predicate_can_decide_what_is_retryable():
    calls = {"n": 0}

    @build_retry(
        operation="op",
        retry_on=lambda e: isinstance(e, FakeHttpError),
        max_attempts=3,
        wait_min_seconds=0,
        wait_max_seconds=0,
    )
    def flaky():
        calls["n"] += 1
        if calls["n"] < 2:
            raise FakeHttpError(500)
        return "done"

    assert flaky() == "done"


def test_rate_limit_callback_is_invoked():
    seen = []

    @build_retry(
        operation="op",
        retry_on=RateLimitError,
        max_attempts=3,
        wait_min_seconds=0,
        wait_max_seconds=0,
        rate_limit_callback=seen.append,
    )
    def limited():
        if len(seen) < 1:
            raise RateLimitError("429")
        return "through"

    assert limited() == "through"
    assert len(seen) == 1


@pytest.mark.parametrize(
    "preset,raises",
    [
        # The two presets deliberately retry different things: the Azure preset covers
        # transient network failures as well as throttling, while the AI preset exists for
        # Azure OpenAI rate-limit storms and retries RateLimitError only.
        (retry_azure_transient, NetworkError),
        (retry_azure_transient, RateLimitError),
        (retry_ai_transient, RateLimitError),
    ],
)
def test_presets_retry_what_they_are_for(preset, raises):
    calls = {"n": 0}

    @preset(operation="op", max_attempts=3, wait_min_seconds=0, wait_max_seconds=0)
    def flaky():
        calls["n"] += 1
        if calls["n"] < 2:
            raise raises("blip")
        return "ok"

    assert flaky() == "ok"
    assert calls["n"] == 2


def test_the_ai_preset_does_not_retry_network_errors():
    """It is for rate-limit storms; a network failure is someone else's problem."""
    calls = {"n": 0}

    @retry_ai_transient(operation="op", max_attempts=5, wait_min_seconds=0, wait_max_seconds=0)
    def flaky():
        calls["n"] += 1
        raise NetworkError("blip")

    with pytest.raises(NetworkError):
        flaky()
    assert calls["n"] == 1
