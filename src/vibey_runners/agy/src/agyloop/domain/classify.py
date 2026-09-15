# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Pure classification of Gemini turn signals into a CapacityState.

There is no typed rate-limit event (F7). Classification is an inference
ladder over whatever structured fields the adapter recovered, with
versioned message markers as a fallback. Ambiguity defaults to a bounded
probe (WindowExhausted unknown), never to Available.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from agyloop.domain.capacity import (
    AuthenticationFailed,
    Available,
    CapacityState,
    CreditsExhausted,
    TransientThrottle,
    WindowExhausted,
)
from agyloop.domain.waiting import next_pacific_midnight

_AUTH_STATUSES = frozenset({"UNAUTHENTICATED", "PERMISSION_DENIED"})

# Versioned spend/billing markers. A pattern that stops matching must fail a
# test rather than silently reclassify a billing wall as a waitable window.
_SPEND_MARKERS = (
    "spend-based rate limit",
    "spend-based",
    "spend limit",
    "billing cap",
    "no balance",
    "usage-credits",
    "purchase more credits",
    "out of extra usage",
    "hard exhaustion",
)

_DAILY_MESSAGE = re.compile(
    r"\b(?:requests per day|daily quota|per day|rpd)\b",
    re.IGNORECASE,
)
_TPM_MESSAGE = re.compile(r"\b(?:tokens per minute|tpm)\b", re.IGNORECASE)
_IPM_MESSAGE = re.compile(r"\b(?:images per minute|ipm)\b", re.IGNORECASE)
_RPM_MESSAGE = re.compile(r"\b(?:requests per minute|rpm)\b", re.IGNORECASE)

# Operator cancel in message/output. Do not match a bare "canceled".
_OPERATOR_CANCEL_MARKERS = (
    "context canceled",
    "context cancelled",
    "manage_task",
)

_WITHDRAWN_PHRASE = "no longer available to new users"
_HTTP_NOT_FOUND = re.compile(r"\b404\b")
_RPC_NOT_FOUND = re.compile(r"\bNOT_FOUND\b")
WITHDRAWN_INPUT_DETECTION_MODEL = "gemini-2.5-flash-lite"


def _current_time() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class QuotaViolation:
    """One google.rpc.QuotaFailure.violations[] entry recovered by the adapter."""

    quota_id: str | None = None
    quota_metric: str | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class TurnSignals:
    """Everything the classifier needs from one turn.

    Assembled by the adapter, never by the domain. Extra optional fields are
    ignored until a later task enriches them; the brief tests only require
    http_status, status, message, and quota_metric.
    """

    http_status: int | None = None
    status: str | None = None
    message: str | None = None
    quota_metric: str | None = None
    exception_type: str | None = None
    exception_message: str | None = None
    google_status: str | None = None
    error_code: str | None = None
    retry_info_delay: timedelta | None = None
    quota_violations: tuple[QuotaViolation, ...] = ()
    tool_error_messages: tuple[str, ...] = ()
    finish_reason: str | None = None
    can_purchase: bool | None = None


def _status(signals: TurnSignals) -> str:
    return (signals.status or signals.google_status or "").upper()


def _message(signals: TurnSignals) -> str:
    return signals.message or signals.exception_message or ""


def looks_like_spend_limit(text: str | None) -> bool:
    """True when copy describes a billing spend or usage-credit wall."""
    if not text:
        return False
    lowered = text.casefold()
    return any(marker in lowered for marker in _SPEND_MARKERS)


def looks_like_operator_cancel(text: str | None) -> bool:
    """True when copy names a programmatic cancel, not a bare ``canceled``."""
    if not text:
        return False
    lowered = text.casefold()
    return any(marker in lowered for marker in _OPERATOR_CANCEL_MARKERS)


def looks_like_withdrawn_model(text: str | None) -> bool:
    """True when copy is a 404 / NOT_FOUND / withdrawn-model failure."""
    if not text:
        return False
    if _WITHDRAWN_PHRASE in text.casefold():
        return True
    if _HTTP_NOT_FOUND.search(text) is not None:
        return True
    return _RPC_NOT_FOUND.search(text) is not None


def _compact(value: str) -> str:
    return re.sub(r"[\s_\-:/]", "", value).casefold()


def _window_kind_from_token(value: str | None) -> str | None:
    if not value:
        return None
    compact = _compact(value)
    if compact in {"rpd"} or "perday" in compact or "requestsperday" in compact:
        return "rpd"
    if compact in {"tpm"} or "tokensperminute" in compact:
        return "tpm"
    if compact in {"ipm"} or "imagesperminute" in compact:
        return "ipm"
    if compact in {"rpm"} or "perminute" in compact or "requestsperminute" in compact:
        return "rpm"
    return None


def _window_kind_from_message(text: str) -> str | None:
    if _DAILY_MESSAGE.search(text):
        return "rpd"
    if _TPM_MESSAGE.search(text):
        return "tpm"
    if _IPM_MESSAGE.search(text):
        return "ipm"
    if _RPM_MESSAGE.search(text):
        return "rpm"
    return None


def _window_kind_from_violations(violations: tuple[QuotaViolation, ...]) -> str | None:
    for violation in violations:
        kind = _window_kind_from_token(violation.quota_id) or _window_kind_from_token(
            violation.quota_metric
        )
        if kind is not None:
            return kind
    return None


def _window(kind: str, now: datetime, quota_id: str | None = None) -> WindowExhausted:
    resets_at = next_pacific_midnight(now) if kind == "rpd" else None
    return WindowExhausted(rate_limit_type=kind, resets_at=resets_at, quota_id=quota_id)


@dataclass(frozen=True, slots=True)
class Classification:
    """Capacity state plus the ladder rung that produced it.

    ``rung`` is a stable identifier for ``doctor explain-classify`` and golden
    fixtures — not a user-facing sentence.
    """

    state: CapacityState
    rung: str


def classify(signals: TurnSignals, now: datetime | None = None) -> CapacityState:
    return classify_explained(signals, now=now).state


def classify_explained(signals: TurnSignals, now: datetime | None = None) -> Classification:
    instant = now if now is not None else _current_time()
    status = _status(signals)
    message = _message(signals)
    http_status = signals.http_status

    # Operator/programmatic cancel is not a capacity signal (F7). Message
    # markers run before the throttle ladder so a 429 plus manage_task cancel
    # cannot become TransientThrottle.
    if signals.exception_type and "cancelled" in signals.exception_type.casefold():
        return Classification(Available(), "operator_cancel")
    if looks_like_operator_cancel(message) or looks_like_operator_cancel(signals.exception_message):
        return Classification(Available(), "operator_cancel")

    # 1. Auth first. Terminal. Never retried.
    if http_status in {401, 403} or status in _AUTH_STATUSES:
        return Classification(
            AuthenticationFailed(detail=message, reason=status or str(http_status or "")),
            "authentication",
        )

    # 7-before-5: 503 / UNAVAILABLE is never CreditsExhausted (F9.3).
    if http_status == 503 or status == "UNAVAILABLE":
        return Classification(
            TransientThrottle(retry_after=signals.retry_info_delay),
            "unavailable",
        )

    spend = looks_like_spend_limit(message)

    rejected = (
        http_status == 429
        or status == "RESOURCE_EXHAUSTED"
        or spend
        or signals.error_code in {"rate_limit_exceeded", "quota_exceeded"}
        or bool(signals.quota_metric)
        or bool(signals.quota_violations)
        or signals.retry_info_delay is not None
    )
    if not rejected:
        return Classification(Available(), "available")

    # 5. Billing / spend markers. Brief: spend-based language is CreditsExhausted,
    # not a 10-minute WindowExhausted. Checked before window construction so a
    # billing marker can never produce a state carrying resets_at.
    if spend:
        purchase = True if signals.can_purchase is None else signals.can_purchase
        return Classification(
            CreditsExhausted(detail=message, can_purchase=purchase),
            "spend",
        )

    # quota_metric is a structured field (brief) — treat like quotaId.
    metric_kind = _window_kind_from_token(signals.quota_metric)
    if metric_kind is not None:
        return Classification(
            _window(metric_kind, instant, quota_id=signals.quota_metric),
            "quota_metric",
        )

    # 2. Structured error_code.
    if signals.error_code == "quota_exceeded":
        return Classification(_window("rpd", instant), "error_code_quota_exceeded")
    if signals.error_code == "rate_limit_exceeded":
        return Classification(
            TransientThrottle(retry_after=signals.retry_info_delay, quota_id=signals.error_code),
            "error_code_rate_limit_exceeded",
        )

    # 3. QuotaFailure.violations[].quotaId.
    violation_kind = _window_kind_from_violations(signals.quota_violations)
    if violation_kind is not None:
        return Classification(_window(violation_kind, instant), "quota_violations")

    # 4. RetryInfo.retryDelay presence is evidence of transience.
    if signals.retry_info_delay is not None:
        return Classification(
            TransientThrottle(retry_after=signals.retry_info_delay),
            "retry_info",
        )

    # 6. Daily / per-minute markers in the message.
    message_kind = _window_kind_from_message(message)
    if message_kind is not None:
        return Classification(_window(message_kind, instant), "message_window")

    # 8. Ambiguous 429 RESOURCE_EXHAUSTED → unknown window, never Available.
    return Classification(WindowExhausted(rate_limit_type="unknown"), "unknown_window")
