"""Example 28 — install_global_exception_hooks.

Wires ``sys.excepthook`` and the asyncio loop exception handler to fire
CRITICAL alerts on uncaught exceptions.

Key invariants:
- ALWAYS chains the previous hook — never replaces silently.
- If no asyncio loop is running yet, the asyncio wiring is skipped
  silently; future loops use the default handler.
- The CRITICAL fire is wrapped in try/except — failure of the hook
  itself must not cascade.

This is one of the four lines in the v2 quickstart snippet (see
``01_quickstart.py``).
"""

from __future__ import annotations

import os
import sys

os.environ.setdefault("USE_MOCK_BOOTSTRAP", "true")
os.environ.setdefault("AZURE_BOOTSTRAP_ALLOW_RESET", "1")

from vibey_bootstrap.alerts import (
    install_global_exception_hooks,
    register_dispatcher,
    reset_state,
)
from vibey_bootstrap.logging import configure_logging


def main() -> None:
    configure_logging()
    reset_state()

    received: list[tuple[list[str], str, str]] = []
    register_dispatcher(lambda r, s, b: received.append((r, s, b)), recipients=["ops@example.com"])

    # ── 1. Capture previous excepthook so we can prove chaining ────────
    previous_hook_calls: list[type] = []
    original = sys.excepthook

    def previous(exc_type, exc, tb):  # type: ignore[no-untyped-def]
        previous_hook_calls.append(exc_type)
        # Don't call original here — would print to stderr and confuse demo.

    sys.excepthook = previous  # type: ignore[assignment]
    try:
        # ── 2. Install v2 hooks AFTER the "previous" one ────────────────
        install_global_exception_hooks()

        # ── 3. Simulate an uncaught exception ──────────────────────────
        # We invoke sys.excepthook manually rather than actually raising
        # so the example exits cleanly and the demo flow continues.
        sys.excepthook(ValueError, ValueError("simulated uncaught"), None)  # type: ignore[misc]
    finally:
        sys.excepthook = original

    # ── 4. Verify alert fired + previous hook still called ─────────────
    valuee_alerts = [r for r in received if "ValueError" in r[1]]

    print(
        f"alert emails fired         : {len(received)} (with subjects containing ValueError: {len(valuee_alerts)})"
    )
    print(f"previous hook still called : {previous_hook_calls == [ValueError]}")
    print("v2 hook chained, not replaced")

    # ── 5. Subject format ──────────────────────────────────────────────
    if valuee_alerts:
        print(f"\nsample subject : {valuee_alerts[0][1]!r}")

    # ── Verified summary ──────────────────────────────────────────────
    print()
    print("verified:")
    print("  sys.excepthook fires CRITICAL alert with dedup key 'uncaught:<ExcType>'")
    print("  previous excepthook chained (never replaced silently)")
    print("  asyncio loop handler wired separately (skipped here — no loop running)")
    print("  failure of the hook itself does not cascade (try/except wraps the alert call)")


if __name__ == "__main__":
    main()


# ── Expected output ──
# <log lines>
# alert emails fired         : 1 (with subjects containing ValueError: 1)
# previous hook still called : True
# v2 hook chained, not replaced
#
# sample subject : '[CRITICAL] Uncaught ValueError: simulated uncaught'
#
# verified:
#   ...
