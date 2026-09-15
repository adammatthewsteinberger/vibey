"""NCRONTAB → APScheduler CronTrigger parser.

Requires the ``scheduler`` extra (``apscheduler``). Falls back to
``CronTrigger(minute='*/15')`` on any parse failure — apps prefer "runs less
often than expected" over "fails to start" for non-critical schedules.
"""

from __future__ import annotations

import logging
from typing import Any

from vibey_bootstrap.tracing.decorators import traced

_logger = logging.getLogger(__name__)
_DEFAULT_TRIGGER_SPEC: dict[str, str] = {"minute": "*/15"}


def _default_trigger() -> Any:
    from apscheduler.triggers.cron import CronTrigger  # type: ignore[import-not-found]

    return CronTrigger(**_DEFAULT_TRIGGER_SPEC)


@traced(operation="scheduler.parse_cron_trigger")
def parse_cron_trigger(expr: str) -> Any:
    """Parse a 5- or 6-field NCRONTAB into a CronTrigger.

    Empty/whitespace input returns the default ``minute='*/15'`` trigger.
    """
    try:
        from apscheduler.triggers.cron import CronTrigger  # type: ignore[import-not-found]
    except ImportError as exc:
        raise ImportError(
            "parse_cron_trigger requires the `scheduler` extra: "
            "pip install vibey-bootstrap[scheduler]"
        ) from exc

    try:
        stripped = (expr or "").strip()
        if not stripped:
            return CronTrigger(**_DEFAULT_TRIGGER_SPEC)
        fields = stripped.split()
        if len(fields) == 6:
            second, minute, hour, day, month, day_of_week = fields
            return CronTrigger(
                second=second,
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week,
            )
        if len(fields) == 5:
            return CronTrigger.from_crontab(stripped)
        raise ValueError(f"unsupported cron field count: {len(fields)}")
    except Exception as exc:  # noqa: BLE001
        _logger.warning(
            "scheduler: failed to parse cron expression, using default",
            extra={"expr": expr, "exception_type": type(exc).__name__},
        )
        try:
            from vibey_bootstrap.alerts import AlertSeverity, alert_dev_team

            alert_dev_team(
                AlertSeverity.WARN,
                subject=f"Failed to parse cron expression: {type(exc).__name__}",
                context={"expr": expr, "error": str(exc)[:300]},
                dedup_key=f"scheduler.parse_cron_trigger:{type(exc).__name__}",
            )
        except Exception:
            pass
        return CronTrigger(**_DEFAULT_TRIGGER_SPEC)


__all__ = ["parse_cron_trigger"]
