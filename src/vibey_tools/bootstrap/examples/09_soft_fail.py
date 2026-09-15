"""Example 09 — Soft-fail helpers.

Wrap fragile sub-features (AI summarization, optional enrichment, etc.)
in ``soft_fail_with()`` or ``soft_fail()`` so a single sub-feature failure
produces a degraded result rather than killing the pipeline.

Key invariants:
- Unrecoverable exceptions (per ``is_unrecoverable``) propagate by default
  — soft-failing an ``InvalidMessageError`` would break the dead-letter
  contract. Set ``re_raise_unrecoverable=False`` to opt out explicitly.
- Counter bump + ERROR alert fire on the soft-fail path; the alert is
  best-effort (failure to dispatch never breaks the caller).
"""

from __future__ import annotations

import os

os.environ.setdefault("USE_MOCK_BOOTSTRAP", "true")
os.environ.setdefault("AZURE_BOOTSTRAP_ALLOW_RESET", "1")

from vibey_bootstrap.alerts import (
    drain_pending_alerts,
    register_dispatcher,
)
from vibey_bootstrap.alerts import reset_state as reset_alerts
from vibey_bootstrap.counters import _reset_counters, counter_snapshot
from vibey_bootstrap.exceptions import InvalidMessageError
from vibey_bootstrap.logging import configure_logging
from vibey_bootstrap.softfail import soft_fail, soft_fail_with


def summarize(text: str) -> str:
    """Imagine this calls Azure OpenAI; it's flaky in this example."""
    raise RuntimeError("upstream timeout")


def main() -> None:
    configure_logging()
    _reset_counters()
    reset_alerts()
    register_dispatcher(lambda *a: None, recipients=["ops@example.com"])

    # ── 1. soft_fail_with — return form ────────────────────────────────
    result = soft_fail_with(
        summarize,
        "long document body...",
        fallback="(summary unavailable)",
        operation="ai.summary",
        counter_name="ai.summary.failed",
    )
    print(f"soft_fail_with result: degraded={result.degraded} value={result.value!r}")
    print(f"  reason: {result.reason}")

    # ── 2. soft_fail context-manager form ──────────────────────────────
    with soft_fail(operation="enrichment.lookup", counter_name="enrichment.failed") as ctx:
        raise ValueError("flaky 3rd-party API")
    print(f"\nsoft_fail ctx exit: degraded={ctx['degraded']} reason={ctx['reason']}")

    # ── 3. Unrecoverable MUST propagate (poison-message defense) ───────
    try:
        soft_fail_with(
            lambda: (_ for _ in ()).throw(InvalidMessageError("malformed payload")),
            fallback=None,
            operation="parse.payload",
        )
    except InvalidMessageError as exc:
        print(f"\nunrecoverable re-raised: {type(exc).__name__}: {exc}")

    # ── 4. Opt-out path (rare; documented in code review) ──────────────
    out = soft_fail_with(
        lambda: (_ for _ in ()).throw(InvalidMessageError("anyway")),
        fallback=42,
        operation="parse.payload.lenient",
        re_raise_unrecoverable=False,
    )
    print(f"\nopted-out unrecoverable: value={out.value}")

    counters = counter_snapshot()
    pending = drain_pending_alerts()

    # ── Verified summary ───────────────────────────────────────────────
    print()
    print("verified:")
    print(f"  ai.summary.failed counter   : {counters.get('ai.summary.failed', 0)}")
    print(f"  enrichment.failed counter   : {counters.get('enrichment.failed', 0)}")
    print(f"  ERROR alerts queued         : {len(pending)}")
    print("  InvalidMessageError propagated when re_raise_unrecoverable=True (default)")


if __name__ == "__main__":
    main()


# ── Expected output ──
# soft_fail_with result: degraded=True value='(summary unavailable)'
#   reason: RuntimeError
#
# soft_fail ctx exit: degraded=True reason=ValueError
#
# unrecoverable re-raised: InvalidMessageError: malformed payload
#
# opted-out unrecoverable: value=42
#
# verified:
#   ai.summary.failed counter   : 1
#   enrichment.failed counter   : 1
#   ERROR alerts queued         : 2
#   InvalidMessageError propagated when re_raise_unrecoverable=True (default)
