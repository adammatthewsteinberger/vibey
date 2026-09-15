"""Dynamic log-level refresh via App Configuration.

Wire ``refresh_log_flags`` into APScheduler at ``CronTrigger(minute='*')`` so
ops can flip the App Config key and see it take effect within 60s without
redeploying.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Iterable

from vibey_bootstrap.counters import bump_counter
from vibey_bootstrap.logging.config import configure_logging, effective_log_level

_logger = logging.getLogger(__name__)


def _mock_enabled() -> bool:
    return os.environ.get("USE_MOCK_BOOTSTRAP", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def refresh_log_flags(
    settings: Iterable[str] = ("DEBUG_LOGGING_ENABLED", "LOG_LEVEL"),
) -> None:
    """Re-read named settings from App Config, then reapply logging if the
    effective level changed. Best-effort end-to-end.
    """
    if _mock_enabled():
        return
    try:
        prev_level = logging.getLogger().getEffectiveLevel()

        # Step 1: read remote settings via the v2 ``refresh_setting`` hook.
        try:
            import vibey_bootstrap

            refresh = getattr(vibey_bootstrap, "refresh_setting", None)
            if callable(refresh):
                refresh(*settings)
            else:
                _logger.debug("log_flag_refresh: no refresh_setting available")
        except ImportError:
            _logger.debug("log_flag_refresh: no bootstrap importable")
        except Exception as exc:  # noqa: BLE001
            bump_counter("log_flag_refresh.remote_read_failed")
            _logger.warning(
                "log_flag_refresh: remote read raised",
                extra={"exception_type": type(exc).__name__, "error": str(exc)[:300]},
            )
            try:
                from vibey_bootstrap.alerts import AlertSeverity, alert_dev_team

                alert_dev_team(
                    AlertSeverity.WARN,
                    subject="App Config refresh raised inside refresh_log_flags",
                    context={
                        "exception_type": type(exc).__name__,
                        "error": str(exc)[:300],
                    },
                    dedup_key="log_flag_refresh_remote_failed",
                )
            except Exception:
                pass

        # Step 2: re-apply logging if the level actually changed.
        target_level = effective_log_level()
        if target_level != prev_level:
            bump_counter("log_flag_refresh.level_changed")
            _logger.info(
                "log_flag_refresh: re-applying logging",
                extra={
                    "operation": "log_flag_refresh",
                    "prev_level": prev_level,
                    "new_level": target_level,
                },
            )
            configure_logging()
        else:
            _logger.debug("log_flag_refresh: no level change")
    except Exception:
        bump_counter("log_flag_refresh.crashed")
        _logger.exception("log_flag_refresh: crashed")


__all__ = ["refresh_log_flags"]
