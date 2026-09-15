"""Example 26 — Service Bus message-lock management.

Wraps ``AutoLockRenewer`` for the duration of message processing so the
broker doesn't redeliver mid-process. Default ``max_lock_renewal_seconds=3600``
covers the longest AI-inclusive pipeline.

Key invariants:
- Renewer ALWAYS closed in ``finally`` (daemon-thread leaks cause priority
  inversion).
- Construction failure is SWALLOWED — the renewer is defense, not a
  correctness gate. If it can't start, processing still runs.
- Two flavors: ``lock_for_process`` context manager + ``ManagedLock`` OO
  variant for multi-stage handlers that want explicit lifetime control.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

os.environ.setdefault("USE_MOCK_BOOTSTRAP", "true")
os.environ.setdefault("AZURE_BOOTSTRAP_ALLOW_RESET", "1")

from vibey_bootstrap.counters import _reset_counters, counter_snapshot
from vibey_bootstrap.sb_lock import (
    DEFAULT_MAX_LOCK_RENEWAL_SECONDS,
    ManagedLock,
    lock_for_process,
)


def main() -> None:
    _reset_counters()

    # We patch the real AutoLockRenewer factory because this example
    # doesn't speak to a live Service Bus.
    renewer_calls: list[str] = []

    class FakeRenewer:
        def register(self, receiver, msg, *, max_lock_renewal_duration):
            renewer_calls.append(f"register({max_lock_renewal_duration})")

        def close(self):
            renewer_calls.append("close()")

    # ── 1. Context-manager form ────────────────────────────────────────
    with patch(
        "vibey_bootstrap.sb_lock._new_auto_lock_renewer",
        return_value=FakeRenewer(),
    ):
        with lock_for_process(MagicMock(name="receiver"), MagicMock(name="msg")):
            # Imagine a 30+ second AI call here
            pass
    print(f"ctx-manager:  renewer calls = {renewer_calls}")

    # ── 2. Closes on exception too ─────────────────────────────────────
    renewer_calls.clear()
    with patch(
        "vibey_bootstrap.sb_lock._new_auto_lock_renewer",
        return_value=FakeRenewer(),
    ):
        try:
            with lock_for_process(MagicMock(), MagicMock()):
                raise RuntimeError("processor crashed")
        except RuntimeError:
            pass
    print(f"on exception: renewer calls = {renewer_calls} (close MUST appear)")

    # ── 3. Construction failure swallowed ──────────────────────────────
    with patch(
        "vibey_bootstrap.sb_lock._new_auto_lock_renewer",
        side_effect=RuntimeError("AutoLockRenewer init failed"),
    ):
        # Block must still run even though renewer setup failed
        ran = False
        with lock_for_process(MagicMock(), MagicMock()):
            ran = True
        print(f"construction failure: processing still ran? {ran}")

    # ── 4. ManagedLock OO variant ──────────────────────────────────────
    renewer_calls.clear()
    with patch(
        "vibey_bootstrap.sb_lock._new_auto_lock_renewer",
        return_value=FakeRenewer(),
    ):
        lock = ManagedLock(
            MagicMock(name="receiver"),
            MagicMock(name="msg"),
            max_lock_renewal_seconds=900,
        )
        lock.start()
        # ... stage one ...
        # ... stage two ...
        lock.close()
    print(f"ManagedLock:  renewer calls = {renewer_calls}")

    counters = counter_snapshot()

    # ── Verified summary ──────────────────────────────────────────────
    print()
    print("verified:")
    print(f"  DEFAULT_MAX_LOCK_RENEWAL_SECONDS    : {DEFAULT_MAX_LOCK_RENEWAL_SECONDS} (1 hour)")
    print(f"  sb_lock.renewer_started counter     : {counters.get('sb_lock.renewer_started', 0)}")
    print(
        f"  sb_lock.renewer_construction_failed : {counters.get('sb_lock.renewer_construction_failed', 0)}"
    )
    print("  close ALWAYS called in finally")


if __name__ == "__main__":
    main()


# ── Expected output ──
# ctx-manager:  renewer calls = ['register(3600)', 'close()']
# on exception: renewer calls = ['register(3600)', 'close()'] (close MUST appear)
# construction failure: processing still ran? True
# ManagedLock:  renewer calls = ['register(900)', 'close()']
#
# verified:
#   ...
