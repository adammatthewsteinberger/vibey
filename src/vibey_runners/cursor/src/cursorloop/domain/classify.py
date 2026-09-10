# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Classify Cursor turn signals into capacity states and faults.

Branch order is load-bearing and must not be shuffled. Auth outranks billing
(enforced by ``test_authentication_outranks_everything_including_billing``);
billing outranks any stray Retry-After window (enforced by
``test_credits_beat_a_stray_retry_after``).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from cursorloop.domain.capacity import (
    AuthenticationFailed,
    Available,
    CapacityState,
    CreditsExhausted,
    WindowExhausted,
)
from cursorloop.domain.faults import Busy, ConfigFault, Fault, TransientFault
from cursorloop.domain.lexicon import (
    DEFAULT_BILLING_TERMS,
    DEFAULT_RATE_LIMIT_TERMS,
    BillingLexicon,
    RateLimitLexicon,
)
from cursorloop.domain.retry_after import parse_retry_after

UNCLASSIFIED_REASON = "unclassified_terminal_error"

_AUTH_TYPES = frozenset({"AuthenticationError", "PermissionDeniedError"})
_TRANSIENT_KINDS = {
    "NetworkError": "network",
    "APITimeoutError": "timeout",
    "InternalServerError": "server",
}
_CONFIG_TYPES = frozenset(
    {
        "ConfigurationError",
        "BadRequestError",
        "IntegrationNotConnectedError",
    }
)
_AUDIT_NOW = datetime(1970, 1, 1, tzinfo=UTC)


@dataclass(frozen=True, slots=True)
class TurnSignals:
    error_type: str | None = None  # class name, e.g. "RateLimitError"
    error_code: str | None = None  # CursorAgentError.code
    proto_error_code: str | None = None
    error_message: str = ""
    http_status: int | None = None  # status_code
    is_retryable: bool | None = None
    retry_after: str | None = None
    run_status: str | None = None  # "finished"|"error"|"cancelled"|"expired"|"running"
    result_text: str = ""
    request_id: str | None = None


def classify(
    signals: TurnSignals,
    *,
    now: datetime,
    billing: BillingLexicon | None = None,
    rate_limit: RateLimitLexicon | None = None,
) -> CapacityState | Fault:
    billing_lex, rate_limit_lex = _resolve_lexicons(billing, rate_limit)

    # 1. auth/permission → AuthenticationFailed
    if signals.error_type in _AUTH_TYPES:
        return AuthenticationFailed(detail=signals.error_message)

    # 2. billing lexicon (code, proto code, message, or result_text when
    #    status is "error") → CreditsExhausted. HTTP 402 is Payment Required.
    if signals.http_status == 402 or billing_lex.matches(*_billing_channels(signals)):
        return CreditsExhausted(can_purchase=True)

    # 3. RateLimitError with is_retryable is False → CreditsExhausted
    if signals.error_type == "RateLimitError" and signals.is_retryable is False:
        return CreditsExhausted(can_purchase=True)

    # 4. RateLimitError / HTTP 429 → WindowExhausted
    if signals.error_type == "RateLimitError" or signals.http_status == 429:
        return WindowExhausted("rate_limit", parse_retry_after(signals.retry_after, now=now))

    # 5. run_status == "error" + rate-limit lexicon → unscheduled window
    if signals.run_status == "error" and rate_limit_lex.matches(*_rate_limit_channels(signals)):
        return WindowExhausted("rate_limit", None)

    # 6. run_status == "expired" → WindowExhausted("run_expired", None)
    if signals.run_status == "expired":
        return WindowExhausted("run_expired", None)

    # 7. AgentBusyError → Busy; retryable network/timeout/5xx → TransientFault;
    #    ConfigurationError / BadRequestError / IntegrationNotConnectedError → ConfigFault
    if signals.error_type == "AgentBusyError":
        return Busy(agent_id="", active_run_id=None)

    if signals.is_retryable is True:
        kind = _transient_kind(signals)
        if kind is not None:
            return TransientFault(kind=kind, attempt_hint=1)

    if signals.error_type in _CONFIG_TYPES:
        return ConfigFault(detail=signals.error_message)

    # 8. otherwise → Available
    return Available()


def classification_reason(
    signals: TurnSignals,
    *,
    billing: BillingLexicon | None = None,
    rate_limit: RateLimitLexicon | None = None,
) -> str:
    """Return an audit marker for this classification.

    When ``run_status == "error"`` and no earlier branch matched, ``classify``
    returns ``Available`` and this helper prefixes ``UNCLASSIFIED_REASON`` onto
    the verbatim signal text so the audit layer can log unmatched wording.
    """
    if signals.run_status != "error":
        return ""
    outcome = classify(signals, now=_AUDIT_NOW, billing=billing, rate_limit=rate_limit)
    if not isinstance(outcome, Available):
        return ""
    detail = signals.result_text or signals.error_message
    if detail:
        return f"{UNCLASSIFIED_REASON}: {detail}"
    return UNCLASSIFIED_REASON


def _resolve_lexicons(
    billing: BillingLexicon | None,
    rate_limit: RateLimitLexicon | None,
) -> tuple[BillingLexicon, RateLimitLexicon]:
    if billing is None:
        billing = BillingLexicon(DEFAULT_BILLING_TERMS)
    if rate_limit is None:
        rate_limit = RateLimitLexicon(DEFAULT_RATE_LIMIT_TERMS)
    return billing, rate_limit


def _billing_channels(signals: TurnSignals) -> tuple[str | None, ...]:
    channels: list[str | None] = [
        signals.error_code,
        signals.proto_error_code,
        signals.error_message,
    ]
    if signals.run_status == "error":
        channels.append(signals.result_text)
    return tuple(channels)


def _rate_limit_channels(signals: TurnSignals) -> tuple[str | None, ...]:
    return (
        signals.result_text,
        signals.error_message,
        signals.error_code,
        signals.proto_error_code,
    )


def _transient_kind(signals: TurnSignals) -> str | None:
    if signals.error_type is not None:
        kind = _TRANSIENT_KINDS.get(signals.error_type)
        if kind is not None:
            return kind
    if signals.http_status is not None and signals.http_status >= 500:
        return "server"
    return None
