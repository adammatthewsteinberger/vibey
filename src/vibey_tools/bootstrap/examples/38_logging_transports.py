"""Example 38 — Logging transport layer (console / App Insights / Sumo Logic).

v2.1 adds a transport registry: each log sink is a named ``logging.Handler``
factory you can turn on or off from your own code (or via an env flag).

- ``configure_transports(console=…, app_insights=…, sumo_logic=…)`` is the
  high-level toggle. An explicit boolean wins; otherwise the per-transport env
  flag is consulted (``CONSOLE_LOGGING_ENABLED`` / ``APP_INSIGHTS_LOGGING_ENABLED``
  / ``SUMO_LOGIC_LOGGING_ENABLED``).
- The Sumo Logic transport is a buffered, background-thread, batched HTTP POST
  of newline-delimited JSON to a Sumo HTTP Source. It never blocks and never
  raises; it ships via ``requests`` + a ``urllib3`` Retry adapter (backoff,
  ``Retry-After``, gzip). Install the ``[sumologic]`` extra and set
  ``SUMO_LOGIC_COLLECTOR_URL`` to enable it; absent the URL (or the extra),
  enabling it is a safe no-op.
- ``register_transport`` lets you add your own named sink.

The registry, console, and App Insights transports need no extra; the Sumo Logic
transport needs ``pip install 'vibey-bootstrap[sumologic]'``.
"""

from __future__ import annotations

import logging
import os

os.environ.setdefault("USE_MOCK_BOOTSTRAP", "true")
os.environ.setdefault("AZURE_BOOTSTRAP_ALLOW_RESET", "1")

from vibey_bootstrap import (
    configure_transports,
    list_transports,
    register_transport,
)
from vibey_bootstrap.logging import JsonLogFormatter, correlation_scope


def main() -> None:
    logger = logging.getLogger("example.transports")

    # Console on, App Insights + Sumo off (no connection string / collector URL here).
    configure_transports(console=True, app_insights=False, sumo_logic=False)
    with correlation_scope(request_id="req-42"):
        logger.info("console transport active", extra={"user_id": "u1"})

    # Register a custom in-memory transport that captures JSON lines.
    captured: list[str] = []

    class _CaptureHandler(logging.Handler):
        def __init__(self) -> None:
            super().__init__()
            self.setFormatter(JsonLogFormatter())

        def emit(self, record: logging.LogRecord) -> None:
            captured.append(self.format(record))

    register_transport("capture", _CaptureHandler, replace=True)
    from vibey_bootstrap import enable_transport

    enable_transport("capture")
    logger.warning("shipped as JSON", extra={"api_key": "supersecret", "order_id": 7})

    snapshot = list_transports()
    masked = '"api_key": "***"' in captured[-1]

    # ── Verified summary ───────────────────────────────────────────────
    print("verified:")
    print(f"  console enabled      : {snapshot['console']['enabled']}")
    print(f"  app_insights enabled : {snapshot['app_insights']['enabled']}")
    print(f"  sumo_logic enabled   : {snapshot['sumo_logic']['enabled']}")
    print(f"  custom captured lines: {len(captured)}")
    print(f"  api_key masked in JSON: {masked}")

    from vibey_bootstrap.transports import _reset_transports

    _reset_transports()  # closes handlers / joins Sumo thread


if __name__ == "__main__":
    main()


# ── Expected output ──
# <console line> console transport active  user_id='u1' correlation_id='…' request_id='req-42'
# <console line> shipped as JSON  api_key='supersecret' order_id=7
# verified:
#   console enabled      : True
#   app_insights enabled : False
#   sumo_logic enabled   : False
#   custom captured lines: 1
#   api_key masked in JSON: True
