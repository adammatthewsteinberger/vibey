# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Pure classification of raw turn signals into a CapacityState.

This is the direct replacement for `extract_limit_signals()` in the legacy script
(legacy/claude_autoresume.py:290-333), except it operates on typed fields the
Agent SDK already parsed, instead of regexing a raw JSON stream. `rate_limit_status
== "allowed_warning"` is deliberately NOT checked as a rejection signal — it falls
through the `rejected` computation below to `Available`, so it can never be
mistaken for a hard limit. Once rejected, credit signals are checked before
falling back to WindowExhausted, so a credits rejection can never be mistaken for
a waitable window even if a stray resets_at rides along with it.

`assistant_error == "billing_error"` (SDK AssistantMessageError) is treated like
credits exhaustion — checked before the Available / window path so a billing
failure cannot be classified as Available or WindowExhausted.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from claudeloop.domain.capacity import (
    AuthenticationFailed,
    Available,
    CapacityState,
    CreditsExhausted,
    WindowExhausted,
)

_CREDITS_ERROR_CODES = frozenset({"credits_required"})
_CREDITS_DISABLED_REASONS = frozenset({"out_of_credits"})

# Monthly spend / usage-credit limit copy often arrives as a bare rate_limit + 429
# (or only as ResultMessage.result text) with RateLimitEvent dropped — never treat
# that as a waitable window.
#
# Markers must be error-phrasing, not topic mentions: a turn that *documents*
# "monthly spend limit" / "spend limit" / "/usage-credits" must stay Available.
# Bare "you've hit your" also matches session/weekly window copy and must not
# force CreditsExhausted on its own.
_SPEND_LIMIT_ERROR_MARKERS = (
    "hit your monthly",
    "out of extra usage",
    "purchase more credits",
)


def looks_like_spend_limit(text: str | None) -> bool:
    """True when assistant/result copy is a billing spend / usage-credit *error*."""
    if not text:
        return False
    lowered = text.casefold()
    return any(marker in lowered for marker in _SPEND_LIMIT_ERROR_MARKERS)


@dataclass(frozen=True, slots=True)
class TurnSignals:
    """Everything the classifier needs from one turn, gathered from the Agent SDK's
    RateLimitEvent, ResultMessage, and AssistantMessage — deliberately not a single
    source, because RateLimitEvent is reportedly dropped on some adapter paths."""

    rate_limit_status: str | None = None  # "allowed" | "allowed_warning" | "rejected"
    rate_limit_type: str | None = None
    resets_at: datetime | None = None
    utilization: float | None = None
    overage_status: str | None = None
    overage_resets_at: datetime | None = None
    overage_disabled_reason: str | None = None
    api_error_status: int | None = None
    assistant_error: str | None = None
    error_code: str | None = None
    disabled_reason: str | None = None
    can_purchase: bool | None = None
    result_text: str | None = None


def classify(signals: TurnSignals) -> CapacityState:
    if signals.assistant_error == "authentication_failed":
        return AuthenticationFailed(detail=signals.assistant_error)

    # SDK AssistantMessageError sibling of authentication_failed / rate_limit.
    # Billing failures have no reset clock — never treat as WindowExhausted
    # even when a stray resets_at or 429 rides along.
    if signals.assistant_error == "billing_error":
        return CreditsExhausted(can_purchase=True)

    spend_limit = looks_like_spend_limit(signals.result_text)

    rejected = (
        signals.rate_limit_status == "rejected"
        or signals.api_error_status == 429
        or signals.assistant_error == "rate_limit"
        or spend_limit
    )

    if not rejected:
        return Available(utilization=signals.utilization)

    if (
        signals.error_code in _CREDITS_ERROR_CODES
        or signals.disabled_reason in _CREDITS_DISABLED_REASONS
        or signals.overage_disabled_reason is not None
        or spend_limit
    ):
        can_purchase = True if signals.can_purchase is None else signals.can_purchase
        return CreditsExhausted(can_purchase=can_purchase)

    resets_at = signals.resets_at or signals.overage_resets_at
    return WindowExhausted(
        rate_limit_type=signals.rate_limit_type or "unknown",
        resets_at=resets_at,
    )
