"""Example 10 — Per-phase guarded execution.

``run_phase`` wraps each stage of a multi-stage pipeline so one phase's
bug can't nuke the whole run. The phase's exception is caught, logged,
counted, and (optionally) alerted — then the caller decides what to do
with the failed ``PhaseResult``.

Key invariants:
- ``run_phase`` NEVER re-raises. Always returns a ``PhaseResult``.
- Counter conventions:
  ``{namespace}.{name}.ok`` on success,
  ``{namespace}.{name}.failed`` on exception,
  ``{namespace}.{name}.{aggregate_counter}`` += ``len(result)`` when the
  result is sized.
"""

from __future__ import annotations

import os

os.environ.setdefault("USE_MOCK_BOOTSTRAP", "true")
os.environ.setdefault("AZURE_BOOTSTRAP_ALLOW_RESET", "1")

from vibey_bootstrap.alerts import register_dispatcher
from vibey_bootstrap.alerts import reset_state as reset_alerts
from vibey_bootstrap.counters import _reset_counters, counter_snapshot
from vibey_bootstrap.logging import configure_logging
from vibey_bootstrap.phases import run_phase, run_phases


# ── Simulated pipeline stages ──────────────────────────────────────────
def collect_pages() -> list[dict]:
    return [{"page": i, "text": f"page {i} text"} for i in range(1, 6)]


def analyze_text() -> None:
    raise RuntimeError("third-party analyzer crashed")


def render_report() -> list[str]:
    return ["report.pdf", "report-summary.html"]


def main() -> None:
    configure_logging()
    _reset_counters()
    reset_alerts()
    register_dispatcher(lambda *a: None, recipients=["ops@example.com"])

    # ── Single phase, aggregate-counter form ─────────────────────────
    pr = run_phase(
        "collect",
        collect_pages,
        namespace="deficiency",
        aggregate_counter="pages",
        alert_severity=None,
    )
    print(f"collect: ok={pr.ok} pages={len(pr.value or [])} elapsed={pr.elapsed_seconds}s")

    # ── Multi-phase pipeline; failure isolated to its phase ───────────
    results = run_phases(
        [
            ("analyze", analyze_text),  # raises → contributes nothing
            ("render", render_report),  # still runs after the failure
        ],
        namespace="deficiency",
        alert_severity=None,
    )

    for r in results:
        status = "ok" if r.ok else f"failed ({type(r.exception).__name__})"
        print(f"{r.name:10}: {status}")

    counters = counter_snapshot()

    # ── Verified summary ─────────────────────────────────────────────
    print()
    print("verified:")
    print(f"  deficiency.collect.ok      : {counters.get('deficiency.collect.ok', 0)}")
    print(f"  deficiency.collect.pages   : {counters.get('deficiency.collect.pages', 0)}")
    print(f"  deficiency.analyze.failed  : {counters.get('deficiency.analyze.failed', 0)}")
    print(f"  deficiency.render.ok       : {counters.get('deficiency.render.ok', 0)}")
    print("  run_phase never re-raised  : True (caller got PhaseResult instead)")


if __name__ == "__main__":
    main()


# ── Expected output ──
# collect: ok=True pages=5 elapsed=<small float>
# analyze   : failed (RuntimeError)
# render    : ok
#
# verified:
#   deficiency.collect.ok      : 1
#   deficiency.collect.pages   : 5
#   deficiency.analyze.failed  : 1
#   deficiency.render.ok       : 1
#   run_phase never re-raised  : True (caller got PhaseResult instead)
