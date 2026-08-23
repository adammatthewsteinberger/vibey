# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Vendor error -> vibey's CapacityState, and exit code + tail -> FailureClass
(rotation-and-engines.md §6.2-6.3).

The four runners emit the *loop family's shared CapacityState shape in
spirit (domain/capacity.py's docstring: "inherited from the *loop family,
unchanged in spirit"), but each vendor's own error payload -- what actually
comes back from the provider before the runner normalizes it -- has a
different shape. No real captured vendor payloads were available while
building this (no live accounts, no docker to run the real binaries), so
the per-engine parsers below encode a plausible, clearly-documented shape
per vendor; they are the seam a real captured-payload fixture would replace
without touching anything above classify_capacity's call site.

What is load-bearing and *is* tested exhaustively here: credits and window
exhaustion are never confused, regardless of which engine's payload shape
produced the classification -- that is the one rule the whole `*loop`
family exists to protect (domain/circuit.py's property test enforces the
downstream half; this module is the upstream half).
"""

import re
from collections.abc import Mapping
from datetime import UTC, datetime

from vibey.domain.capacity import (
    AuthenticationFailed,
    Available,
    CapacityState,
    CreditsExhausted,
    WindowExhausted,
)
from vibey.domain.engine import EngineId
from vibey.domain.job import FailureClass

_WORK_MARKERS = (
    "FAILED ",
    "AssertionError",
    "assert ",
    "pytest",
    "Test failed",
    "compile error",
    "SyntaxError",
)
_ENGINE_MARKERS = (
    "Traceback (most recent call last)",
    "panic:",
    "Segmentation fault",
    "core dumped",
    "unexpected EOF",
    "runner crashed",
)
_VIBEY_MARKERS = ("VibeyInternalError",)


def _classify_claudeloop(raw: Mapping[str, object]) -> CapacityState:
    capacity = raw.get("capacity")
    if not isinstance(capacity, Mapping):
        return Available()
    state = capacity.get("state")
    if state == "credits_exhausted":
        return CreditsExhausted(can_purchase=bool(capacity.get("can_purchase", True)))
    if state == "window_exhausted":
        resets_at = capacity.get("resets_at")
        return WindowExhausted(
            resets_at=_parse_dt(resets_at), rate_limit_type=capacity.get("rate_limit_type")
        )
    if state == "auth_failed":
        return AuthenticationFailed(detail=str(capacity.get("detail", "")))
    return Available()


def _classify_codexloop(raw: Mapping[str, object]) -> CapacityState:
    error = raw.get("error")
    if not isinstance(error, Mapping):
        return Available()
    code = error.get("code")
    if code == "insufficient_quota":
        return CreditsExhausted(can_purchase=True)
    if code == "rate_limit_exceeded":
        return WindowExhausted(resets_at=_parse_dt(error.get("reset_at")), rate_limit_type="rpm")
    if code in ("invalid_api_key", "unauthorized"):
        return AuthenticationFailed(detail=str(error.get("message", "")))
    return Available()


def _classify_cursorloop(raw: Mapping[str, object]) -> CapacityState:
    status = raw.get("status")
    kind = raw.get("type")
    if status == 402 or kind == "credits_exhausted":
        return CreditsExhausted(can_purchase=bool(raw.get("can_purchase", True)))
    if status == 429 or kind == "rate_limited":
        retry_after = raw.get("retry_after_seconds")
        resets_at = None
        if isinstance(retry_after, int | float):
            from datetime import timedelta

            resets_at = datetime.now(UTC) + timedelta(seconds=retry_after)
        return WindowExhausted(resets_at=resets_at, rate_limit_type="requests")
    if status == 401 or kind == "unauthorized":
        return AuthenticationFailed(detail=str(raw.get("message", "")))
    return Available()


def _classify_agyloop(raw: Mapping[str, object]) -> CapacityState:
    grpc_status = raw.get("grpc_status")
    if grpc_status == "RESOURCE_EXHAUSTED":
        quota_metric = str(raw.get("quota_metric", ""))
        if "billing" in quota_metric or raw.get("billing_exhausted"):
            return CreditsExhausted(can_purchase=True)
        retry_after = raw.get("retry_after")
        resets_at = _parse_duration_from_now(retry_after) if retry_after else None
        return WindowExhausted(resets_at=resets_at, rate_limit_type=quota_metric or None)
    if grpc_status == "UNAUTHENTICATED":
        return AuthenticationFailed(detail=str(raw.get("detail", "")))
    return Available()


def _classify_qwenloop(raw: Mapping[str, object]) -> CapacityState:
    """Normalize qwenloop's local lifecycle states.

    The credits shape exists only for shared conformance testing; qwenloop's
    runtime never emits it for a local resource or configuration failure.
    """
    state = raw.get("local_state")
    if state == "credits_exhausted":
        return CreditsExhausted(can_purchase=False)
    if state == "busy":
        return WindowExhausted(resets_at=_parse_dt(raw.get("retry_at")), rate_limit_type="local")
    if state == "configuration_error":
        return AuthenticationFailed(detail=str(raw.get("detail", "")))
    return Available()


_CLASSIFIERS = {
    EngineId.CLAUDELOOP: _classify_claudeloop,
    EngineId.CODEXLOOP: _classify_codexloop,
    EngineId.CURSORLOOP: _classify_cursorloop,
    EngineId.AGYLOOP: _classify_agyloop,
    EngineId.QWENLOOP: _classify_qwenloop,
}


def classify_capacity(engine_id: EngineId, raw: Mapping[str, object]) -> CapacityState:
    return _CLASSIFIERS[engine_id](raw)


# Fixture corpus shared by the classifier's own tests and the conformance
# suite's capacity_map check (rotation-and-engines.md §8.2). Synthesized
# per-vendor shapes -- see module docstring for why these are not captured
# real payloads.
CREDITS_FIXTURES: dict[EngineId, dict[str, object]] = {
    EngineId.CLAUDELOOP: {"capacity": {"state": "credits_exhausted", "can_purchase": True}},
    EngineId.CODEXLOOP: {"error": {"code": "insufficient_quota", "message": "quota exceeded"}},
    EngineId.CURSORLOOP: {"status": 402, "type": "credits_exhausted", "can_purchase": True},
    EngineId.AGYLOOP: {
        "grpc_status": "RESOURCE_EXHAUSTED",
        "quota_metric": "billing.generate_content",
        "billing_exhausted": True,
    },
    EngineId.QWENLOOP: {"local_state": "credits_exhausted"},
}

WINDOW_FIXTURES: dict[EngineId, dict[str, object]] = {
    EngineId.CLAUDELOOP: {
        "capacity": {
            "state": "window_exhausted",
            "resets_at": "2026-01-01T00:05:00+00:00",
            "rate_limit_type": "rpm",
        }
    },
    EngineId.CODEXLOOP: {
        "error": {"code": "rate_limit_exceeded", "reset_at": "2026-01-01T00:05:00+00:00"}
    },
    EngineId.CURSORLOOP: {"status": 429, "type": "rate_limited", "retry_after_seconds": 60},
    EngineId.AGYLOOP: {
        "grpc_status": "RESOURCE_EXHAUSTED",
        "quota_metric": "generate_content_free_tier_requests",
        "retry_after": "30s",
    },
    EngineId.QWENLOOP: {"local_state": "busy", "retry_at": "2026-01-01T00:05:00+00:00"},
}

AUTH_FIXTURES: dict[EngineId, dict[str, object]] = {
    EngineId.CLAUDELOOP: {"capacity": {"state": "auth_failed", "detail": "expired key"}},
    EngineId.CODEXLOOP: {"error": {"code": "invalid_api_key", "message": "bad key"}},
    EngineId.CURSORLOOP: {"status": 401, "type": "unauthorized", "message": "bad token"},
    EngineId.AGYLOOP: {"grpc_status": "UNAUTHENTICATED", "detail": "adc not found"},
    EngineId.QWENLOOP: {"local_state": "configuration_error", "detail": "model missing"},
}

AVAILABLE_FIXTURES: dict[EngineId, dict[str, object]] = {
    EngineId.CLAUDELOOP: {},
    EngineId.CODEXLOOP: {},
    EngineId.CURSORLOOP: {"status": 200},
    EngineId.AGYLOOP: {"grpc_status": "OK"},
    EngineId.QWENLOOP: {"local_state": "available"},
}


def _parse_dt(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    return datetime.fromisoformat(value)


def _parse_duration_from_now(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    match = re.match(r"^(\d+)s$", value)
    if not match:
        return None
    from datetime import timedelta

    return datetime.now(UTC) + timedelta(seconds=int(match.group(1)))


def attribute_failure(exit_code: int, tail: str) -> FailureClass:
    """Attribution order matters: a WORK-class signal (the project's own
    test suite failing) must win even if the tail also contains an
    incidental traceback, because a failing pytest must never open the
    engine's circuit."""
    if any(marker in tail for marker in _WORK_MARKERS):
        return FailureClass.WORK
    if any(marker in tail for marker in _VIBEY_MARKERS):
        return FailureClass.VIBEY
    if exit_code == 0:
        return FailureClass.WORK
    if any(marker in tail for marker in _ENGINE_MARKERS) or exit_code in (124, 137, -9):
        return FailureClass.ENGINE
    return FailureClass.WORK
