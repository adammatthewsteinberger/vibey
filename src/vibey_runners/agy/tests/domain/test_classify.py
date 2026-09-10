# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from datetime import timedelta

from hypothesis import assume, given
from hypothesis import strategies as st

from agyloop.domain.capacity import (
    AuthenticationFailed,
    Available,
    CreditsExhausted,
    TransientThrottle,
    WindowExhausted,
)
from agyloop.domain.classify import (
    QuotaViolation,
    TurnSignals,
    classify,
    looks_like_operator_cancel,
)
from agyloop.domain.waiting import next_pacific_midnight

# --- Brief tests (verbatim) ---


def test_rpm_resource_exhausted_is_window():
    state = classify(
        TurnSignals(
            http_status=429,
            status="RESOURCE_EXHAUSTED",
            message="Resource exhausted: RPM",
            quota_metric="rpm",
        )
    )
    assert isinstance(state, WindowExhausted)
    assert state.rate_limit_type == "rpm"


def test_spend_limit_is_credits():
    state = classify(
        TurnSignals(
            http_status=429,
            status="RESOURCE_EXHAUSTED",
            message="spend-based rate limit",
        )
    )
    assert isinstance(state, CreditsExhausted)


def test_rpd_uses_pacific_midnight(fake_now):
    state = classify(
        TurnSignals(
            http_status=429,
            status="RESOURCE_EXHAUSTED",
            message="requests per day",
            quota_metric="rpd",
        )
    )
    assert isinstance(state, WindowExhausted)
    assert state.rate_limit_type == "rpd"


# --- Ladder and invariants ---


def test_rpd_resets_at_is_next_pacific_midnight(fake_now):
    state = classify(
        TurnSignals(
            http_status=429,
            status="RESOURCE_EXHAUSTED",
            message="requests per day",
            quota_metric="rpd",
        ),
        now=fake_now,
    )
    assert isinstance(state, WindowExhausted)
    assert state.resets_at == next_pacific_midnight(fake_now)


def test_bare_429_resource_exhausted_is_unknown_window() -> None:
    state = classify(
        TurnSignals(
            http_status=429,
            status="RESOURCE_EXHAUSTED",
            message="Resource has been exhausted (e.g. check quota).",
        )
    )
    assert isinstance(state, WindowExhausted)
    assert state.rate_limit_type == "unknown"
    assert state.resets_at is None


def test_auth_401_is_authentication_failed() -> None:
    state = classify(TurnSignals(http_status=401, message="invalid API key"))
    assert isinstance(state, AuthenticationFailed)


def test_auth_403_is_authentication_failed() -> None:
    state = classify(
        TurnSignals(http_status=403, status="PERMISSION_DENIED", message="permission denied")
    )
    assert isinstance(state, AuthenticationFailed)


def test_unauthenticated_status_is_authentication_failed() -> None:
    state = classify(TurnSignals(http_status=401, status="UNAUTHENTICATED"))
    assert isinstance(state, AuthenticationFailed)


def test_503_unavailable_is_transient_throttle() -> None:
    state = classify(TurnSignals(http_status=503, status="UNAVAILABLE", message="model overloaded"))
    assert isinstance(state, TransientThrottle)


def test_503_with_spend_language_is_still_transient_throttle() -> None:
    state = classify(
        TurnSignals(
            http_status=503,
            status="UNAVAILABLE",
            message="spend-based rate limit while overloaded",
        )
    )
    assert isinstance(state, TransientThrottle)
    assert not isinstance(state, CreditsExhausted)


def test_rate_limit_exceeded_is_transient_throttle() -> None:
    state = classify(
        TurnSignals(
            http_status=429,
            status="RESOURCE_EXHAUSTED",
            error_code="rate_limit_exceeded",
        )
    )
    assert isinstance(state, TransientThrottle)


def test_quota_exceeded_is_rpd_window(fake_now) -> None:
    state = classify(
        TurnSignals(
            http_status=429,
            status="RESOURCE_EXHAUSTED",
            error_code="quota_exceeded",
        ),
        now=fake_now,
    )
    assert isinstance(state, WindowExhausted)
    assert state.rate_limit_type == "rpd"
    assert state.resets_at == next_pacific_midnight(fake_now)


def test_retry_info_delay_is_transient_throttle() -> None:
    delay = timedelta(seconds=27)
    state = classify(
        TurnSignals(
            http_status=429,
            status="RESOURCE_EXHAUSTED",
            retry_info_delay=delay,
        )
    )
    assert isinstance(state, TransientThrottle)
    assert state.retry_after == delay


def test_quota_violation_per_day_is_rpd(fake_now) -> None:
    state = classify(
        TurnSignals(
            http_status=429,
            status="RESOURCE_EXHAUSTED",
            quota_violations=(QuotaViolation(quota_id="GenerateRequestsPerDayPerProjectPerModel"),),
        ),
        now=fake_now,
    )
    assert isinstance(state, WindowExhausted)
    assert state.rate_limit_type == "rpd"
    assert state.resets_at == next_pacific_midnight(fake_now)


def test_quota_violation_per_minute_is_rpm_window() -> None:
    state = classify(
        TurnSignals(
            http_status=429,
            status="RESOURCE_EXHAUSTED",
            quota_violations=(
                QuotaViolation(quota_id="GenerateRequestsPerMinutePerProjectPerModel"),
            ),
        )
    )
    assert isinstance(state, WindowExhausted)
    assert state.rate_limit_type == "rpm"


def test_tpm_quota_metric_is_window() -> None:
    state = classify(
        TurnSignals(
            http_status=429,
            status="RESOURCE_EXHAUSTED",
            quota_metric="tpm",
        )
    )
    assert isinstance(state, WindowExhausted)
    assert state.rate_limit_type == "tpm"


def test_rpm_message_without_metric_is_window() -> None:
    state = classify(
        TurnSignals(
            http_status=429,
            status="RESOURCE_EXHAUSTED",
            message="You've exceeded the API's rate limits (RPM).",
        )
    )
    assert isinstance(state, WindowExhausted)
    assert state.rate_limit_type == "rpm"


def test_tpm_and_ipm_from_message() -> None:
    tpm = classify(
        TurnSignals(
            http_status=429,
            status="RESOURCE_EXHAUSTED",
            message="tokens per minute quota exceeded",
        )
    )
    assert isinstance(tpm, WindowExhausted)
    assert tpm.rate_limit_type == "tpm"
    ipm = classify(
        TurnSignals(
            http_status=429,
            status="RESOURCE_EXHAUSTED",
            message="images per minute quota exceeded",
        )
    )
    assert isinstance(ipm, WindowExhausted)
    assert ipm.rate_limit_type == "ipm"


def test_unknown_quota_metric_falls_through_to_unknown_window() -> None:
    state = classify(
        TurnSignals(
            http_status=429,
            status="RESOURCE_EXHAUSTED",
            quota_metric="something-else",
        )
    )
    assert isinstance(state, WindowExhausted)
    assert state.rate_limit_type == "unknown"


def test_spend_can_purchase_passthrough() -> None:
    state = classify(
        TurnSignals(
            http_status=429,
            status="RESOURCE_EXHAUSTED",
            message="spend-based rate limit",
            can_purchase=False,
        )
    )
    assert isinstance(state, CreditsExhausted)
    assert state.can_purchase is False


def test_daily_quota_message_is_rpd(fake_now) -> None:
    state = classify(
        TurnSignals(
            http_status=429,
            status="RESOURCE_EXHAUSTED",
            message="Exceeded your daily quota",
        ),
        now=fake_now,
    )
    assert isinstance(state, WindowExhausted)
    assert state.rate_limit_type == "rpd"


def test_success_is_available() -> None:
    state = classify(TurnSignals(http_status=200, status="OK"))
    assert isinstance(state, Available)


def test_empty_signals_are_available() -> None:
    assert isinstance(classify(TurnSignals()), Available)


def test_cancelled_exception_is_not_capacity() -> None:
    state = classify(
        TurnSignals(
            exception_type="AntigravityCancelledError",
            message="turn cancelled",
        )
    )
    assert isinstance(state, Available)


def test_context_canceled_by_manage_task_is_not_throttle() -> None:
    from agyloop.domain.classify import classify_explained

    result = classify_explained(
        TurnSignals(
            exception_type="AntigravityExecutionError",
            message="429 RESOURCE_EXHAUSTED context canceled by manage_task",
            http_status=429,
            status="RESOURCE_EXHAUSTED",
        )
    )
    assert isinstance(result.state, Available)
    assert result.rung == "operator_cancel"


def test_bare_canceled_is_not_operator_cancel() -> None:
    from agyloop.domain.classify import classify_explained

    result = classify_explained(
        TurnSignals(
            http_status=429,
            status="RESOURCE_EXHAUSTED",
            message="request canceled",
        )
    )
    assert isinstance(result.state, WindowExhausted)
    assert result.rung != "operator_cancel"


def test_credits_exhausted_has_no_resets_at() -> None:
    state = classify(
        TurnSignals(
            http_status=429,
            status="RESOURCE_EXHAUSTED",
            message="spend-based rate limit",
        )
    )
    assert isinstance(state, CreditsExhausted)
    assert not hasattr(state, "resets_at")


def test_quota_metric_rpm_outranks_rate_limit_exceeded() -> None:
    state = classify(
        TurnSignals(
            http_status=429,
            status="RESOURCE_EXHAUSTED",
            message="Resource exhausted: RPM",
            quota_metric="rpm",
            error_code="rate_limit_exceeded",
        )
    )
    assert isinstance(state, WindowExhausted)
    assert state.rate_limit_type == "rpm"


@given(st.text(max_size=40))
def test_spend_marker_never_yields_resets_at(prefix: str) -> None:
    assume(not looks_like_operator_cancel(prefix))
    state = classify(
        TurnSignals(
            http_status=429,
            status="RESOURCE_EXHAUSTED",
            message=f"{prefix}spend-based rate limit",
        )
    )
    assert isinstance(state, CreditsExhausted)
    assert not hasattr(state, "resets_at")


@given(
    st.one_of(st.none(), st.text(max_size=60)),
    st.one_of(st.none(), st.sampled_from(["rpm", "rpd", "tpm", "ipm"])),
)
def test_resource_exhausted_never_available(message: str | None, quota_metric: str | None) -> None:
    assume(not looks_like_operator_cancel(message))
    state = classify(
        TurnSignals(
            http_status=429,
            status="RESOURCE_EXHAUSTED",
            message=message,
            quota_metric=quota_metric,
        )
    )
    assert not isinstance(state, Available)
