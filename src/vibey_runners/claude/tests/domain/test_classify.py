# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from datetime import datetime, timezone

from claudeloop.domain.capacity import (
    AuthenticationFailed,
    Available,
    CreditsExhausted,
    WindowExhausted,
)
from claudeloop.domain.classify import TurnSignals, classify

NOW = datetime(2026, 8, 9, tzinfo=timezone.utc)


def test_no_signals_is_available():
    assert classify(TurnSignals()) == Available(utilization=None)


def test_allowed_warning_is_not_a_rejection():
    """The exact false positive documented in the legacy script: allowed_warning
    carries a far-future weekly resetsAt but must never trigger a cooldown."""
    signals = TurnSignals(rate_limit_status="allowed_warning", utilization=0.92)
    result = classify(signals)
    assert isinstance(result, Available)
    assert result.utilization == 0.92


def test_rejected_status_with_reset_time_is_window_exhausted():
    signals = TurnSignals(rate_limit_status="rejected", rate_limit_type="five_hour", resets_at=NOW)
    result = classify(signals)
    assert result == WindowExhausted(rate_limit_type="five_hour", resets_at=NOW)


def test_rejected_status_without_reset_time_falls_back_to_unknown():
    signals = TurnSignals(rate_limit_status="rejected")
    result = classify(signals)
    assert result == WindowExhausted(rate_limit_type="unknown", resets_at=None)


def test_api_error_429_alone_is_rejected():
    """RateLimitEvent is reportedly dropped on some adapter paths — classification
    must not depend on it alone."""
    signals = TurnSignals(api_error_status=429)
    result = classify(signals)
    assert isinstance(result, WindowExhausted)


def test_assistant_error_rate_limit_alone_is_rejected():
    signals = TurnSignals(assistant_error="rate_limit")
    result = classify(signals)
    assert isinstance(result, WindowExhausted)


def test_credits_required_error_code_is_credits_exhausted_not_window():
    """The real transcript case: credits_required has no reset time and must never
    be classified as a waitable window."""
    signals = TurnSignals(
        rate_limit_status="rejected", error_code="credits_required", resets_at=None
    )
    result = classify(signals)
    assert result == CreditsExhausted(can_purchase=True)


def test_out_of_credits_disabled_reason_is_credits_exhausted():
    signals = TurnSignals(rate_limit_status="rejected", disabled_reason="out_of_credits")
    assert classify(signals) == CreditsExhausted(can_purchase=True)


def test_overage_disabled_reason_is_credits_exhausted():
    signals = TurnSignals(rate_limit_status="rejected", overage_disabled_reason="disabled")
    assert classify(signals) == CreditsExhausted(can_purchase=True)


def test_credits_exhausted_even_if_a_reset_time_is_present():
    """Credit signals must outrank a stray reset time — waiting can never fix this."""
    signals = TurnSignals(
        rate_limit_status="rejected", error_code="credits_required", resets_at=NOW
    )
    assert isinstance(classify(signals), CreditsExhausted)


def test_authentication_failed_outranks_everything():
    signals = TurnSignals(
        assistant_error="authentication_failed",
        rate_limit_status="rejected",
        error_code="credits_required",
    )
    result = classify(signals)
    assert result == AuthenticationFailed(detail="authentication_failed")


def test_billing_error_alone_is_credits_exhausted():
    """SDK AssistantMessageError includes billing_error as a sibling of
    rate_limit / authentication_failed. Alone it must not fall through to
    Available."""
    signals = TurnSignals(assistant_error="billing_error")
    assert classify(signals) == CreditsExhausted(can_purchase=True)


def test_billing_error_outranks_window_even_with_resets_at():
    """billing_error + 429 / resets_at must never become waitable WindowExhausted."""
    signals = TurnSignals(
        assistant_error="billing_error",
        api_error_status=429,
        rate_limit_status="rejected",
        resets_at=NOW,
    )
    assert isinstance(classify(signals), CreditsExhausted)


def test_overage_resets_at_used_when_primary_resets_at_absent():
    signals = TurnSignals(
        rate_limit_status="rejected", rate_limit_type="overage", overage_resets_at=NOW
    )
    result = classify(signals)
    assert result == WindowExhausted(rate_limit_type="overage", resets_at=NOW)


def test_spend_limit_result_text_with_thin_rate_limit_is_credits_exhausted():
    """f132e38a attempts 7–10: monthly spend-limit copy + rate_limit/429 and no
    overage_* fields must never become WindowExhausted."""
    signals = TurnSignals(
        assistant_error="rate_limit",
        api_error_status=429,
        result_text=(
            "You've hit your monthly spend limit. Run /usage-credits to manage "
            "your limit and keep using Fable 5 or switch models to continue this chat."
        ),
    )
    assert classify(signals) == CreditsExhausted(can_purchase=True)


def test_spend_limit_text_alone_is_credits_exhausted():
    """Spend-limit copy without a structured rejection still outranks Available."""
    signals = TurnSignals(
        result_text="You've hit your monthly spend limit. Run /usage-credits.",
    )
    assert classify(signals) == CreditsExhausted(can_purchase=True)


def test_ordinary_assistant_text_is_not_spend_limit():
    signals = TurnSignals(result_text="Waiting for the E2E suite to finish.")
    assert classify(signals) == Available(utilization=None)


def test_documenting_spend_limit_is_not_credits_exhausted():
    """Topic mentions must not trip CreditsExhausted — capacity outranks Done,
    so a false positive here aborts otherwise-successful autonomous runs."""
    for text in (
        "Documented the monthly spend limit behavior.",
        "We raised the spend limit in config.",
        "Updated the usage-credits page in the docs.",
        "See /usage-credits in the docs.",
    ):
        assert classify(TurnSignals(result_text=text)) == Available(utilization=None)


def test_session_limit_copy_is_not_spend_limit():
    """Broad 'you've hit your' window copy must stay waitable WindowExhausted."""
    signals = TurnSignals(
        assistant_error="rate_limit",
        api_error_status=429,
        rate_limit_type="five_hour",
        resets_at=NOW,
        result_text="You've hit your session limit. It resets at 4pm.",
    )
    result = classify(signals)
    assert result == WindowExhausted(rate_limit_type="five_hour", resets_at=NOW)


def test_weekly_limit_copy_is_not_spend_limit():
    signals = TurnSignals(
        rate_limit_status="rejected",
        rate_limit_type="seven_day",
        resets_at=NOW,
        result_text="You've hit your weekly limit. Come back later.",
    )
    result = classify(signals)
    assert isinstance(result, WindowExhausted)
