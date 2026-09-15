# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from hypothesis import given
from hypothesis import strategies as st

from cursorloop.domain.capacity import (
    AuthenticationFailed,
    Available,
    CreditsExhausted,
    WindowExhausted,
)
from cursorloop.domain.classify import (
    UNCLASSIFIED_REASON,
    TurnSignals,
    classification_reason,
    classify,
)
from cursorloop.domain.faults import Busy, ConfigFault, TransientFault
from cursorloop.domain.lexicon import (
    DEFAULT_BILLING_TERMS,
    BillingLexicon,
    RateLimitLexicon,
)
from tests.fixtures import signals as signal_fixtures

NOW = datetime(2026, 8, 13, 12, 0, 0, tzinfo=UTC)


def test_credits_beat_a_stray_retry_after() -> None:
    """THE adversarial case. A rejection carrying BOTH a retry_after and a
    billing code must classify as CreditsExhausted: a spend cap does not clear
    because a clock advanced, and treating it as a window is exactly the bug
    this project exists to delete."""
    signals = TurnSignals(
        error_type="RateLimitError",
        error_code="usage_limit_reached",
        error_message="You have reached your monthly usage limit.",
        http_status=429,
        is_retryable=True,
        retry_after="60",
    )
    assert classify(signals, now=NOW) == CreditsExhausted(can_purchase=True)


def test_non_retryable_rate_limit_is_credits() -> None:
    """`is_retryable=False` on a RateLimitError means retrying will never clear
    it — that is an exhausted allowance, not a window."""
    signals = TurnSignals(error_type="RateLimitError", is_retryable=False, http_status=429)
    assert classify(signals, now=NOW) == CreditsExhausted(can_purchase=True)


def test_retryable_rate_limit_with_seconds_is_a_window() -> None:
    signals = TurnSignals(
        error_type="RateLimitError", is_retryable=True, retry_after="120", http_status=429
    )
    assert classify(signals, now=NOW) == WindowExhausted("rate_limit", NOW + timedelta(seconds=120))


def test_retryable_rate_limit_without_header_is_an_unscheduled_window() -> None:
    signals = TurnSignals(error_type="RateLimitError", is_retryable=True, http_status=429)
    assert classify(signals, now=NOW) == WindowExhausted("rate_limit", None)


def test_authentication_outranks_everything_including_billing() -> None:
    signals = TurnSignals(
        error_type="AuthenticationError",
        error_message="invalid api key; also out_of_credits",
        http_status=401,
    )
    assert classify(signals, now=NOW) == AuthenticationFailed(
        detail="invalid api key; also out_of_credits"
    )


def test_permission_denied_is_terminal_not_retried() -> None:
    signals = TurnSignals(error_type="PermissionDeniedError", http_status=403)
    assert isinstance(classify(signals, now=NOW), AuthenticationFailed)


def test_errored_run_status_is_read_even_though_nothing_was_thrown() -> None:
    """The second, non-thrown failure channel: run.wait() returns
    status='error' with free text. A classifier that only catches exceptions
    would score this as a successful turn."""
    signals = TurnSignals(run_status="error", result_text="Rate limit exceeded, slow down.")
    assert classify(signals, now=NOW) == WindowExhausted("rate_limit", None)


def test_errored_run_status_with_billing_text_is_credits() -> None:
    signals = TurnSignals(run_status="error", result_text="Payment required: add credits.")
    assert classify(signals, now=NOW) == CreditsExhausted(can_purchase=True)


def test_live_bridge_out_of_usage_status_copy_is_credits() -> None:
    """Observed Cursor bridge status ERROR when composer quota is spent."""
    signals = TurnSignals(
        run_status="error",
        result_text=(
            "Increase limits for faster responses You're out of usage. "
            "Switch to Auto, or ask your admin to increase your limit to continue."
        ),
    )
    assert classify(signals, now=NOW) == CreditsExhausted(can_purchase=True)


def test_expired_run_is_a_window() -> None:
    assert classify(TurnSignals(run_status="expired"), now=NOW) == WindowExhausted(
        "run_expired", None
    )


def test_cancelled_run_is_not_a_capacity_problem() -> None:
    """We cancelled it (watchdog or operator). Re-sending is correct."""
    assert classify(TurnSignals(run_status="cancelled"), now=NOW) == Available()


def test_agent_busy_is_a_fault_not_capacity_despite_is_retryable_false() -> None:
    """AgentBusyError documents is_retryable=False, yet the remedy is
    cancel-then-resend. Handling it before the generic is_retryable check is
    what stops a naive `if not is_retryable: raise` aborting a recoverable run."""
    signals = TurnSignals(
        error_type="AgentBusyError", error_code="agent_busy", http_status=409, is_retryable=False
    )
    assert classify(signals, now=NOW) == Busy(agent_id="", active_run_id=None)


def test_transient_network_failure_is_a_fault() -> None:
    signals = TurnSignals(error_type="NetworkError", is_retryable=True)
    assert isinstance(classify(signals, now=NOW), TransientFault)


def test_configuration_error_is_terminal_config_fault() -> None:
    signals = TurnSignals(error_type="ConfigurationError", error_message="unknown model 'nope'")
    assert isinstance(classify(signals, now=NOW), ConfigFault)


def test_finished_run_is_available() -> None:
    assert classify(TurnSignals(run_status="finished", result_text="done"), now=NOW) == Available()


@given(term=st.sampled_from(DEFAULT_BILLING_TERMS), seconds=st.integers(1, 100_000))
def test_a_billing_term_never_produces_a_waitable_window(term: str, seconds: int) -> None:
    """The safety property, stated over the whole lexicon rather than a
    handful of examples: nothing carrying billing language may ever become a
    WindowExhausted with a deadline."""
    signals = TurnSignals(
        error_type="RateLimitError",
        error_message=f"error: {term}",
        is_retryable=True,
        retry_after=str(seconds),
        http_status=429,
    )
    assert classify(signals, now=NOW) == CreditsExhausted(can_purchase=True)


def test_unclassified_errored_run_is_available_with_sentinel_reason() -> None:
    """An errored run that matches no lexicon is not a capacity rejection.
    classify returns Available so the loop can proceed, and the audit marker
    carries the unmatched wording verbatim for later harvesting."""
    signals = signal_fixtures.unclassified_errored_run()
    assert classify(signals, now=NOW) == Available()
    reason = classification_reason(signals)
    assert reason.startswith(UNCLASSIFIED_REASON)
    assert "model dumped a stack trace" in reason


def test_empty_unclassified_error_uses_the_sentinel_alone() -> None:
    signals = TurnSignals(run_status="error")
    assert classify(signals, now=NOW) == Available()
    assert classification_reason(signals) == UNCLASSIFIED_REASON


def test_classified_or_finished_signals_carry_no_unclassified_reason() -> None:
    billed = signal_fixtures.errored_run_billing()
    assert UNCLASSIFIED_REASON not in classification_reason(billed)
    assert classification_reason(signal_fixtures.finished_run()) == ""


def test_billing_proto_error_code_is_credits() -> None:
    assert classify(signal_fixtures.billing_via_proto_code(), now=NOW) == CreditsExhausted(
        can_purchase=True
    )


def test_http_429_without_rate_limit_type_is_a_window() -> None:
    assert classify(signal_fixtures.http_429_without_type(), now=NOW) == WindowExhausted(
        "rate_limit", None
    )


def test_http_402_is_credits() -> None:
    assert classify(TurnSignals(http_status=402), now=NOW) == CreditsExhausted(can_purchase=True)


def test_finished_run_does_not_read_billing_from_result_text() -> None:
    signals = TurnSignals(run_status="finished", result_text="add_credits")
    assert classify(signals, now=NOW) == Available()


def test_timeout_and_server_errors_are_transient_faults() -> None:
    timeout = classify(signal_fixtures.timeout_error(), now=NOW)
    assert timeout == TransientFault(kind="timeout", attempt_hint=1)
    server = classify(signal_fixtures.internal_server_error(), now=NOW)
    assert server == TransientFault(kind="server", attempt_hint=1)
    http_5xx = classify(TurnSignals(http_status=503, is_retryable=True), now=NOW)
    assert isinstance(http_5xx, TransientFault)


def test_non_retryable_network_error_is_not_transient() -> None:
    signals = TurnSignals(error_type="NetworkError", is_retryable=False)
    assert classify(signals, now=NOW) == Available()


def test_retryable_success_status_is_not_transient() -> None:
    assert classify(TurnSignals(is_retryable=True, http_status=200), now=NOW) == Available()


def test_bad_request_and_integration_are_config_faults() -> None:
    bad = classify(signal_fixtures.bad_request(), now=NOW)
    assert isinstance(bad, ConfigFault)
    disconnected = classify(signal_fixtures.integration_not_connected(), now=NOW)
    assert isinstance(disconnected, ConfigFault)


def test_configuration_error_carries_the_message() -> None:
    result = classify(signal_fixtures.configuration_error(), now=NOW)
    assert result == ConfigFault(detail="unknown model 'nope'")


def test_network_fault_kind_is_network() -> None:
    result = classify(signal_fixtures.network_error(), now=NOW)
    assert result == TransientFault(kind="network", attempt_hint=1)


def test_billing_lexicon_is_overridable() -> None:
    signals = TurnSignals(error_message="wallet_empty")
    assert classify(signals, now=NOW) == Available()
    billed = classify(signals, now=NOW, billing=BillingLexicon(("wallet_empty",)))
    assert billed == CreditsExhausted(can_purchase=True)


def test_rate_limit_lexicon_is_overridable() -> None:
    signals = TurnSignals(run_status="error", result_text="please throttle")
    assert classify(signals, now=NOW) == Available()
    assert classify(
        signals, now=NOW, rate_limit=RateLimitLexicon(("throttle",))
    ) == WindowExhausted("rate_limit", None)


def test_rate_limit_error_with_unknown_retryable_is_a_window() -> None:
    signals = TurnSignals(error_type="RateLimitError", http_status=429)
    assert classify(signals, now=NOW) == WindowExhausted("rate_limit", None)


def test_retryable_unknown_error_is_available() -> None:
    assert classify(TurnSignals(error_type="OtherError", is_retryable=True), now=NOW) == Available()


def test_retryable_unknown_error_with_5xx_is_transient() -> None:
    result = classify(
        TurnSignals(error_type="OtherError", is_retryable=True, http_status=503), now=NOW
    )
    assert result == TransientFault(kind="server", attempt_hint=1)
