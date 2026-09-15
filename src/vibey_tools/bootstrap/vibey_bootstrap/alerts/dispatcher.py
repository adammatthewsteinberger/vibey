"""Tiered alert dispatcher: WARN (log-only), ERROR (digest + escalation), CRITICAL (email).

Best-effort end-to-end. Every public call is wrapped — alerts are the last
line of defense for an incident, not a new failure mode.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import threading
import time
import traceback
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol

from vibey_bootstrap.alerts.escalation import should_escalate
from vibey_bootstrap.alerts.render import _redact, _render_alert_html
from vibey_bootstrap.counters import bump_counter


class AlertSeverity(str, Enum):
    WARN = "warn"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AlertRecord:
    severity: AlertSeverity
    subject: str
    context: dict[str, Any]
    dedup_key: str
    first_seen: float
    last_seen: float
    count: int = 1
    sent_at: float | None = None


class AlertSender(Protocol):
    def __call__(self, recipients: list[str], subject: str, html_body: str) -> None: ...


@dataclass
class _DispatcherState:
    sender: AlertSender | None = None
    recipients: list[str] = field(default_factory=list)
    dedup: dict[str, AlertRecord] = field(default_factory=dict)
    pending_digest: list[AlertRecord] = field(default_factory=list)
    sent_timestamps: deque[float] = field(default_factory=deque)
    error_history: dict[str, deque[float]] = field(default_factory=dict)
    lock: threading.Lock = field(default_factory=threading.Lock)


_state = _DispatcherState()
_DEDUP_MAX_ENTRIES = 1024
_ERROR_HISTORY_MAXLEN = 64
_logger = logging.getLogger(__name__)


# ── env-var resolvers ──────────────────────────────────────────────────────


def _dedup_window() -> float:
    try:
        return float(os.environ.get("ALERT_DEDUP_WINDOW_SECONDS", "600"))
    except ValueError:
        return 600.0


def _max_per_hour() -> int:
    try:
        return int(os.environ.get("ALERT_MAX_PER_HOUR", "30"))
    except ValueError:
        return 30


def _escalation_threshold() -> int:
    try:
        return int(os.environ.get("ALERT_ESCALATE_AFTER", "5"))
    except ValueError:
        return 5


def _escalation_window() -> float:
    try:
        return float(os.environ.get("ALERT_ESCALATE_WINDOW_SECONDS", "900"))
    except ValueError:
        return 900.0


def _alerts_enabled() -> bool:
    raw = os.environ.get("DEV_ALERTS_ENABLED", "true").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _parse_recipients() -> list[str]:
    raw = os.environ.get("DEV_ALERT_RECIPIENTS", "")
    return [r.strip() for r in raw.split(",") if r.strip()]


def _subject_prefix() -> str:
    return os.environ.get("ALERT_CRITICAL_SUBJECT_PREFIX", "[CRITICAL] ")


# ── Public API ─────────────────────────────────────────────────────────────


def register_dispatcher(
    sender: AlertSender,
    recipients: list[str] | None = None,
) -> None:
    """Wire the alerts module to a live sender. Idempotent."""
    with _state.lock:
        _state.sender = sender
        _state.recipients = list(recipients) if recipients is not None else _parse_recipients()


def alert_dev_team(
    severity: AlertSeverity | str,
    subject: str,
    context: dict[str, Any] | None = None,
    dedup_key: str | None = None,
) -> None:
    """Emit a tiered alert. Best-effort — never raises."""
    try:
        # AlertSeverity subclasses str, so it must be tested for FIRST — an
        # ``isinstance(severity, str)`` check matches the enum too, which left the
        # non-string branch unreachable.
        if isinstance(severity, AlertSeverity):
            sev = severity
        else:
            try:
                sev = AlertSeverity(severity)
            except ValueError:
                sev = AlertSeverity.ERROR
        ctx = dict(context) if context else {}
        key = dedup_key if dedup_key else subject
        now = time.monotonic()

        with _state.lock:
            existing = _state.dedup.get(key)
            if existing is not None and (now - existing.first_seen) <= _dedup_window():
                existing.count += 1
                existing.last_seen = now
                for k, v in ctx.items():
                    existing.context.setdefault(k, v)
                _logger.debug(
                    "alerts: deduped",
                    extra={"operation": "alerts.alert_dev_team", "dedup_key": key},
                )
                return
            rec = AlertRecord(
                severity=sev,
                subject=subject,
                context=ctx,
                dedup_key=key,
                first_seen=now,
                last_seen=now,
            )
            _state.dedup[key] = rec
            if len(_state.dedup) > _DEDUP_MAX_ENTRIES:
                cutoff = now - _dedup_window()
                _state.dedup = {k: v for k, v in _state.dedup.items() if v.last_seen >= cutoff}

        level_map = {
            AlertSeverity.WARN: logging.WARNING,
            AlertSeverity.ERROR: logging.ERROR,
            AlertSeverity.CRITICAL: logging.CRITICAL,
        }
        _logger.log(
            level_map[sev],
            "%s",
            subject,
            extra={
                "operation": "alerts.alert_dev_team",
                "severity": sev.value,
                "dedup_key": key,
                "alert_context": _redact(ctx),
            },
        )

        if sev is AlertSeverity.WARN:
            bump_counter("alerts.warn")
            return

        if sev is AlertSeverity.ERROR:
            bump_counter("alerts.error")
            with _state.lock:
                _state.pending_digest.append(rec)
                history = _state.error_history.setdefault(key, deque(maxlen=_ERROR_HISTORY_MAXLEN))
                escalate = should_escalate(
                    history,
                    threshold=_escalation_threshold(),
                    window_seconds=_escalation_window(),
                )
            if escalate:
                bump_counter("alerts.escalated")
                escalated = AlertRecord(
                    severity=AlertSeverity.CRITICAL,
                    subject=f"[ESCALATED] {subject}",
                    context={
                        **ctx,
                        "_escalation_count": len(history),
                        "_escalation_window_seconds": _escalation_window(),
                    },
                    dedup_key=f"escalated:{key}",
                    first_seen=now,
                    last_seen=now,
                )
                _send_critical(escalated)
            return

        # CRITICAL
        bump_counter("alerts.critical")
        _send_critical(rec)
    except Exception:  # never propagate from alerts
        try:
            _logger.exception("alerts: dispatch failed")
        except Exception:
            pass


def _send_critical(rec: AlertRecord) -> None:
    """Dispatch a CRITICAL email subject to kill-switch + rate-limit checks."""
    try:
        if not _alerts_enabled():
            _logger.warning(
                "alerts: kill switch active (DEV_ALERTS_ENABLED=false), suppressing",
                extra={"dedup_key": rec.dedup_key},
            )
            return

        now = time.monotonic()
        with _state.lock:
            cutoff = now - 3600.0
            while _state.sent_timestamps and _state.sent_timestamps[0] < cutoff:
                _state.sent_timestamps.popleft()
            if len(_state.sent_timestamps) >= _max_per_hour():
                _logger.warning(
                    "alerts: rate-limit hit, folding critical into digest",
                    extra={"dedup_key": rec.dedup_key},
                )
                _state.pending_digest.append(rec)
                return
            sender = _state.sender
            recipients = list(_state.recipients)

        if sender is None or not recipients:
            _logger.warning(
                "alerts: no dispatcher/recipients, recording only",
                extra={"dedup_key": rec.dedup_key},
            )
            with _state.lock:
                _state.pending_digest.append(rec)
            return

        body = _render_alert_html(rec)
        subject = f"{_subject_prefix()}{rec.subject}"
        try:
            sender(recipients, subject, body)
        except Exception:
            _logger.exception(
                "alerts: sender raised, folding into digest",
                extra={"dedup_key": rec.dedup_key},
            )
            with _state.lock:
                _state.pending_digest.append(rec)
            return

        with _state.lock:
            _state.sent_timestamps.append(now)
            rec.sent_at = now
        bump_counter("alerts.critical_emails_sent")
    except Exception:
        try:
            _logger.exception("alerts: _send_critical failed")
        except Exception:
            pass


def drain_pending_alerts() -> list[AlertRecord]:
    """Return and clear the pending-digest list. Used by daily digest builders."""
    with _state.lock:
        out = list(_state.pending_digest)
        _state.pending_digest.clear()
    return out


def install_global_exception_hooks() -> None:
    """Wire ``sys.excepthook`` and the asyncio loop exception handler to fire
    CRITICAL alerts. Always chains to the previous handlers.
    """
    previous_excepthook = sys.excepthook

    def _hook(exc_type: type, exc: BaseException, tb: Any) -> None:
        try:
            alert_dev_team(
                AlertSeverity.CRITICAL,
                subject=f"Uncaught {exc_type.__name__}: {str(exc)[:120]}",
                context={
                    "exception_type": exc_type.__name__,
                    "error": str(exc)[:500],
                    "traceback": "".join(traceback.format_exception(exc_type, exc, tb))[-2000:],
                },
                dedup_key=f"uncaught:{exc_type.__name__}",
            )
        except Exception:
            pass
        try:
            previous_excepthook(exc_type, exc, tb)
        except Exception:
            pass

    sys.excepthook = _hook  # type: ignore[assignment]

    def _async_handler(loop: asyncio.AbstractEventLoop, ctx: dict[str, Any]) -> None:
        try:
            exc = ctx.get("exception")
            exc_type_name = type(exc).__name__ if exc else "AsyncioError"
            msg = ctx.get("message") or (str(exc) if exc else "")
            alert_dev_team(
                AlertSeverity.CRITICAL,
                subject=f"Asyncio uncaught {exc_type_name}: {msg[:120]}",
                context={
                    "exception_type": exc_type_name,
                    "error": str(exc)[:500] if exc else "",
                    "message": str(msg)[:500],
                },
                dedup_key=f"uncaught_async:{exc_type_name}",
            )
        except Exception:
            pass
        try:
            loop.default_exception_handler(ctx)
        except Exception:
            pass

    try:
        loop = asyncio.get_event_loop()
        loop.set_exception_handler(_async_handler)
    except RuntimeError:
        # No event loop yet — future loops will use the default handler.
        pass


def reset_state() -> None:
    """Test-only. Refuses unless AZURE_BOOTSTRAP_ALLOW_RESET=1."""
    if os.environ.get("AZURE_BOOTSTRAP_ALLOW_RESET") != "1":
        raise RuntimeError("reset_state is test-only — set AZURE_BOOTSTRAP_ALLOW_RESET=1")
    with _state.lock:
        _state.sender = None
        _state.recipients = []
        _state.dedup.clear()
        _state.pending_digest.clear()
        _state.sent_timestamps.clear()
        _state.error_history.clear()
