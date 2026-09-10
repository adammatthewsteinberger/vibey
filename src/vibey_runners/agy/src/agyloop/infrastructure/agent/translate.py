# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Translate Antigravity exceptions and chunks into TurnSignals / TurnOutcome.

Errors surface at drain time (F1.1, F7). ``AntigravityCancelledError`` is not
a capacity signal. ``AntigravityValidationError`` is our bug, not a vendor
quota event.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from datetime import timedelta

from google.antigravity.types import AntigravityValidationError

from agyloop.application.dto import TurnOutcome
from agyloop.domain.classify import TurnSignals, looks_like_withdrawn_model
from agyloop.domain.completion import StructuredVerdict
from agyloop.domain.errors import AgentConfigError

_HTTP_STATUS = re.compile(r"\b(401|403|404|408|429|500|503)\b")
_GOOGLE_STATUS = re.compile(
    r"\b(UNAUTHENTICATED|PERMISSION_DENIED|NOT_FOUND|RESOURCE_EXHAUSTED|UNAVAILABLE)\b"
)
_ERROR_CODE = re.compile(r"\b(rate_limit_exceeded|quota_exceeded)\b")
_RETRY_DELAY = re.compile(
    r"retry[_-]?delay[\"']?\s*[:=]\s*[\"']?(\d+(?:\.\d+)?)\s*s",
    re.IGNORECASE,
)


def signals_from_exception(exc: BaseException) -> TurnSignals:
    """Recover structured classifier fields from a vendor exception."""
    message = str(exc)
    http_match = _HTTP_STATUS.search(message)
    status_match = _GOOGLE_STATUS.search(message)
    code_match = _ERROR_CODE.search(message)
    delay_match = _RETRY_DELAY.search(message)
    google_status = status_match.group(1) if status_match else None
    delay: timedelta | None = None
    if delay_match is not None:
        delay = timedelta(seconds=float(delay_match.group(1)))
    return TurnSignals(
        exception_type=type(exc).__name__,
        exception_message=message,
        message=message,
        http_status=int(http_match.group(1)) if http_match else None,
        status=google_status,
        google_status=google_status,
        error_code=code_match.group(1) if code_match else None,
        retry_info_delay=delay,
    )


def outcome_from_exception(
    exc: BaseException,
    *,
    output_text: str = "",
    session_id: str | None = None,
) -> TurnOutcome:
    """Map a drain-time exception to a TurnOutcome, or raise if it is our bug."""
    if isinstance(exc, AntigravityValidationError):
        raise AgentConfigError(str(exc)) from exc
    if looks_like_withdrawn_model(str(exc)):
        raise AgentConfigError(
            "Gemini model is withdrawn or missing (404 / NOT_FOUND). "
            "This is terminal, not Available. "
            f"{exc}"
        ) from exc
    return TurnOutcome(
        signals=signals_from_exception(exc),
        verdict=None,
        output_text=output_text,
        session_id=session_id,
    )


def verdict_from_structured(blob: object) -> StructuredVerdict | None:
    """Map a structured_output() payload to a domain verdict.

    ``None`` means the payload was absent (marker fallback may apply).
    A present but invalid blob is Continue-as-structured so ``evaluate``
    does not fall through to the done marker.
    """
    if blob is None:
        return None
    if not isinstance(blob, dict):
        return StructuredVerdict(complete=False)
    expected_fields = {"complete", "remaining_work", "blocked_on", "summary"}
    if set(blob) != expected_fields:
        return StructuredVerdict(complete=False)

    complete = blob["complete"]
    raw_remaining = blob.get("remaining_work")
    raw_blocked = blob.get("blocked_on")
    summary = blob["summary"]
    if (
        type(complete) is not bool
        or not isinstance(raw_remaining, list)
        or not all(isinstance(item, str) for item in raw_remaining)
        or (raw_blocked is not None and not isinstance(raw_blocked, str))
        or not isinstance(summary, str)
    ):
        return StructuredVerdict(complete=False)

    return StructuredVerdict(
        complete=complete,
        remaining_work=tuple(raw_remaining),
        blocked_on=raw_blocked,
        summary=summary,
    )


def _chunk_text(chunk: object) -> str:
    text = getattr(chunk, "text", None)
    return text if isinstance(text, str) else ""


def outcome_from_chunks(
    chunks: Sequence[object],
    *,
    session_id: str | None = None,
    structured: object | None = None,
) -> TurnOutcome:
    """Reduce semantic chunks to a TurnOutcome. UNKNOWN types are ignored."""
    text_parts: list[str] = []
    for chunk in chunks:
        if type(chunk).__name__ == "Text":
            text_parts.append(_chunk_text(chunk))
    return TurnOutcome(
        signals=TurnSignals(),
        verdict=verdict_from_structured(structured),
        output_text="".join(text_parts),
        session_id=session_id,
    )


def partial_text_from_response(response: object) -> str:
    """Best-effort recovery of Text chunks buffered before a drain error."""
    buffered = getattr(response, "_buffered_chunks", None)
    if not buffered:
        return ""
    return "".join(_chunk_text(chunk) for chunk in buffered if type(chunk).__name__ == "Text")
