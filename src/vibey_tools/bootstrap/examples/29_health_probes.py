"""Example 29 — Framework-neutral health probes.

Three checks that return a small JSON-friendly dict the caller wires into
any HTTP framework's ``/health`` endpoint:

- ``check_app_config_health()``: verify App Config + Key Vault reach.
- ``check_app_insights_health()``: verify the connection string is set.
- ``check_app_insights_logging()``: walk every logger / handler and
  detect an attached Azure Monitor handler.

Each check returns ``{'status': 'ok'|'not_configured'|'error', ...}``.
``USE_MOCK_BOOTSTRAP=true`` adds ``'mock': True`` so dev probes don't
need real Azure.
"""

from __future__ import annotations

import logging
import os

os.environ.setdefault("USE_MOCK_BOOTSTRAP", "true")

from vibey_bootstrap.health import (
    check_app_config_health,
    check_app_insights_health,
    check_app_insights_logging,
)
from vibey_bootstrap.logging import configure_logging


def main() -> None:
    configure_logging()

    # ── 1. Mock mode — every check returns ok + mock ────────────────────
    os.environ["USE_MOCK_BOOTSTRAP"] = "true"
    print("Mock mode (USE_MOCK_BOOTSTRAP=true):")
    print(f"  app_config         : {check_app_config_health()}")
    print(f"  app_insights       : {check_app_insights_health()}")
    print(f"  app_insights_log   : {check_app_insights_logging()}")

    # ── 2. Unconfigured: status='not_configured' ────────────────────────
    os.environ.pop("USE_MOCK_BOOTSTRAP", None)
    for k in (
        "AZURE_APP_CONFIGURATION_CONNECTION_STRING",
        "AZURE_APPCONFIG_ENDPOINT",
        "APPLICATIONINSIGHTS_CONNECTION_STRING",
    ):
        os.environ.pop(k, None)
    print("\nUnconfigured:")
    print(f"  app_config         : {check_app_config_health()}")
    print(f"  app_insights       : {check_app_insights_health()}")
    print(f"  app_insights_log   : {check_app_insights_logging()}")

    # ── 3. Configured + a fake Azure Monitor handler attached ──────────
    os.environ["APPLICATIONINSIGHTS_CONNECTION_STRING"] = (
        "InstrumentationKey=00000000-0000-0000-0000-000000000000"
    )

    class FakeAzureMonitorHandler(logging.Handler):
        """Mimics the class name pattern that App Insights handlers use."""

    handler = FakeAzureMonitorHandler()
    root = logging.getLogger()
    root.addHandler(handler)
    try:
        print("\nWith Azure Monitor handler attached:")
        print(f"  app_insights_log   : {check_app_insights_logging()}")
    finally:
        root.removeHandler(handler)

    # Restore mock mode so this example can be sourced repeatedly
    os.environ["USE_MOCK_BOOTSTRAP"] = "true"

    # ── Verified summary ──────────────────────────────────────────────
    print()
    print("verified:")
    print("  three checks return small JSON-friendly dicts")
    print("  mock mode returns 'mock': True for fast dev probes")
    print("  unconfigured returns 'not_configured' (NOT an error)")
    print("  handler detection walks every named logger + root")


if __name__ == "__main__":
    main()


# ── Expected output ──
# Mock mode (USE_MOCK_BOOTSTRAP=true):
#   app_config         : {'status': 'ok', 'mock': True}
#   app_insights       : {'status': 'ok', 'mock': True}
#   app_insights_log   : {'status': 'ok', 'mock': True}
#
# Unconfigured:
#   app_config         : {'status': 'not_configured'}
#   app_insights       : {'status': 'not_configured'}
#   app_insights_log   : {'status': 'not_configured'}
#
# With Azure Monitor handler attached:
#   app_insights_log   : {'status': 'ok', 'handler': '__main__.FakeAzureMonitorHandler'}
#
# verified:
#   ...
