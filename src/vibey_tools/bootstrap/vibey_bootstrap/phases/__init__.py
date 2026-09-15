"""Per-phase guarded execution for multi-stage pipelines.

The point: one phase's bug must not nuke the whole run. ``run_phase`` always
returns a :class:`PhaseResult` — it never re-raises. Callers inspect the
result and decide what (if anything) to do with a failed phase.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from vibey_bootstrap.counters import bump_counter

T = TypeVar("T")
_logger = logging.getLogger(__name__)


@dataclass
class PhaseResult(Generic[T]):
    name: str
    ok: bool
    value: T | None
    exception: BaseException | None = None
    elapsed_seconds: float | None = None


def _fire_alert(severity: str, namespace: str, name: str, exc: BaseException) -> None:
    try:
        from vibey_bootstrap.alerts import AlertSeverity, alert_dev_team

        alert_dev_team(
            AlertSeverity(severity),
            subject=f"Phase {name} failed: {type(exc).__name__}",
            context={
                "phase": name,
                "namespace": namespace,
                "exception_type": type(exc).__name__,
                "error": str(exc)[:500],
            },
            dedup_key=f"{namespace}.phase.{name}:{type(exc).__name__}",
        )
    except Exception:
        pass


def run_phase(
    name: str,
    fn: Callable[..., T],
    *args: Any,
    namespace: str = "phase",
    alert_severity: str | None = "error",
    aggregate_counter: str | None = None,
    **kwargs: Any,
) -> PhaseResult[T]:
    """Run ``fn`` under a try/except. NEVER re-raises.

    Counters bumped (best-effort):
      - ``{namespace}.{name}.ok`` on success
      - ``{namespace}.{name}.failed`` on exception
      - ``{namespace}.{name}.{aggregate_counter} += len(result)`` when
        ``aggregate_counter`` is given AND the result supports ``len``.
    """
    start = time.monotonic()
    try:
        value = fn(*args, **kwargs)
    except BaseException as exc:
        elapsed = round(time.monotonic() - start, 3)
        _logger.exception(
            "Phase %s raised; contributing nothing",
            name,
            extra={
                "phase": name,
                "namespace": namespace,
                "exception_type": type(exc).__name__,
                "elapsed_seconds": elapsed,
            },
        )
        bump_counter(f"{namespace}.{name}.failed")
        if alert_severity:
            _fire_alert(alert_severity, namespace, name, exc)
        return PhaseResult(name=name, ok=False, value=None, exception=exc, elapsed_seconds=elapsed)

    elapsed = round(time.monotonic() - start, 3)
    bump_counter(f"{namespace}.{name}.ok")
    if aggregate_counter is not None:
        try:
            n = len(value)  # type: ignore[arg-type]
            bump_counter(f"{namespace}.{name}.{aggregate_counter}", n)
        except TypeError:
            pass
    return PhaseResult(name=name, ok=True, value=value, elapsed_seconds=elapsed)


def run_phases(
    phases: list[tuple[str, Callable[..., Any]]],
    *,
    namespace: str = "phase",
    alert_severity: str | None = "error",
) -> list[PhaseResult[Any]]:
    """Run a list of (name, callable) pairs in order, swallowing per-phase
    failures so subsequent phases still execute."""
    return [
        run_phase(name, fn, namespace=namespace, alert_severity=alert_severity)
        for name, fn in phases
    ]


__all__ = ["PhaseResult", "run_phase", "run_phases"]
