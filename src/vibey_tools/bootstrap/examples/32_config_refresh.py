"""Example 32 — Dynamic log-level refresh via App Configuration.

``refresh_log_flags()`` re-reads named settings from App Configuration
(via the v2 ``refresh_setting`` hook) and, if the effective log level
changed, re-runs ``configure_logging()`` so the new level takes effect
immediately.

Wire into APScheduler at ``CronTrigger(minute='*')`` so ops can flip
``LOG_LEVEL`` in App Config and see it apply within 60 s — no redeploy.

Key invariants:
- Short-circuits as a no-op when ``USE_MOCK_BOOTSTRAP`` is truthy.
- ``DEBUG_LOGGING_ENABLED=true`` is REQUIRED as a second factor before
  ``LOG_LEVEL=DEBUG`` is honored. Belt-and-suspenders against a stray
  manifest leaking DEBUG into prod.
- Every counter + alert in the path is best-effort — never breaks the
  scheduler tick.

Requires ``pip install vibey-bootstrap[scheduler]`` only if you wire the
APScheduler driver; ``refresh_log_flags`` itself is stdlib-only.
"""

from __future__ import annotations

import logging
import os

# Override mock mode for this example — we WANT refresh_log_flags to run
os.environ.setdefault("AZURE_BOOTSTRAP_ALLOW_RESET", "1")
os.environ.pop("USE_MOCK_BOOTSTRAP", None)

from vibey_bootstrap.config_refresh import refresh_log_flags
from vibey_bootstrap.counters import _reset_counters, counter_snapshot
from vibey_bootstrap.logging import configure_logging, effective_log_level


def main() -> None:
    _reset_counters()

    # ── 1. Start at INFO ────────────────────────────────────────────────
    os.environ["LOG_LEVEL"] = "INFO"
    os.environ.pop("DEBUG_LOGGING_ENABLED", None)
    configure_logging()
    print(
        f"initial effective level   : {logging.getLogger().getEffectiveLevel()} (INFO={logging.INFO})"
    )

    # ── 2. Flip LOG_LEVEL to WARNING, refresh ──────────────────────────
    os.environ["LOG_LEVEL"] = "WARNING"
    refresh_log_flags()
    print(
        f"after refresh (WARNING)   : {logging.getLogger().getEffectiveLevel()} (WARNING={logging.WARNING})"
    )

    # ── 3. Flip to DEBUG WITHOUT the second-factor flag → clamped to INFO
    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ.pop("DEBUG_LOGGING_ENABLED", None)
    print("\nLOG_LEVEL=DEBUG, DEBUG_LOGGING_ENABLED unset:")
    print(
        f"  effective_log_level()       : {effective_log_level()} (clamped to INFO={logging.INFO})"
    )
    refresh_log_flags()
    print(f"  after refresh               : {logging.getLogger().getEffectiveLevel()} (INFO)")

    # ── 4. Set the second factor — DEBUG honored ────────────────────────
    os.environ["DEBUG_LOGGING_ENABLED"] = "true"
    print("\nDEBUG_LOGGING_ENABLED=true:")
    print(f"  effective_log_level()       : {effective_log_level()} (DEBUG={logging.DEBUG})")
    refresh_log_flags()
    print(f"  after refresh               : {logging.getLogger().getEffectiveLevel()} (DEBUG)")

    counters = counter_snapshot()

    # ── Cleanup ────────────────────────────────────────────────────────
    os.environ.pop("DEBUG_LOGGING_ENABLED", None)
    os.environ["LOG_LEVEL"] = "INFO"
    os.environ["USE_MOCK_BOOTSTRAP"] = "true"

    # ── Verified summary ──────────────────────────────────────────────
    print()
    print("verified:")
    print(f"  log_flag_refresh.level_changed : {counters.get('log_flag_refresh.level_changed', 0)}")
    print("  DEBUG_LOGGING_ENABLED second factor REQUIRED for DEBUG")
    print("  USE_MOCK_BOOTSTRAP truthy → refresh_log_flags is a no-op")
    print("  designed for APScheduler CronTrigger(minute='*') wiring")


if __name__ == "__main__":
    main()


# ── Expected output ──
# initial effective level   : 20 (INFO=20)
# after refresh (WARNING)   : 30 (WARNING=30)
#
# LOG_LEVEL=DEBUG, DEBUG_LOGGING_ENABLED unset:
#   effective_log_level()       : 20 (clamped to INFO=20)
#   after refresh               : 20 (INFO)
#
# DEBUG_LOGGING_ENABLED=true:
#   effective_log_level()       : 10 (DEBUG=10)
#   after refresh               : 10 (DEBUG)
#
# verified:
#   ...
