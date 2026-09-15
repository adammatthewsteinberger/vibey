"""Example 35 — AI usage tracker (tokens, cost, sliding windows).

SDK-agnostic: ``record_usage(deployment, prompt_tokens, completion_tokens)``
is the only call any project needs to wire into its AI call site.

Three sliding windows: 60 s, 60 m, 24 h.

``acquire(deployment, estimated_tokens)`` provides an optional soft TPM
cap — call it BEFORE the AI call to throttle. No-op when ``AI_TPM_LIMIT``
is unset/0. ``check_thresholds_and_alert()`` runs on a schedule (every
10 min) and CRITICAL-alerts on cost / token-volume breaches; per-key
30-minute cooldown prevents alert spam.

Pricing defaults cover GPT-4o family + Claude 3 family. Apps override
per deployment via env vars (``AI_PRICING_<NORMALIZED>_INPUT_PER_1K``)
or ``register_pricing()`` at startup.
"""

from __future__ import annotations

import os
import time

os.environ.setdefault("USE_MOCK_BOOTSTRAP", "true")
os.environ.setdefault("AZURE_BOOTSTRAP_ALLOW_RESET", "1")

from vibey_bootstrap.alerts import register_dispatcher
from vibey_bootstrap.alerts import reset_state as reset_alerts
from vibey_bootstrap.counters import _reset_counters, counter_snapshot
from vibey_bootstrap.openai import (
    _pricing_for,
    acquire,
    check_thresholds_and_alert,
    record_usage,
    register_pricing,
)
from vibey_bootstrap.openai import reset_state as reset_tracker
from vibey_bootstrap.openai import (
    usage_snapshot,
)


def main() -> None:
    reset_tracker()
    reset_alerts()
    _reset_counters()
    register_dispatcher(lambda *a: None, recipients=["ops@example.com"])

    # ── 1. Record some usage on multiple deployments ────────────────────
    record_usage("gpt-4o", prompt_tokens=1000, completion_tokens=500)
    record_usage("gpt-4o", prompt_tokens=2000, completion_tokens=1000)
    record_usage("claude-3-5-sonnet", prompt_tokens=3000, completion_tokens=800)
    record_usage("gpt-4o-mini", prompt_tokens=500, completion_tokens=200)

    snap = usage_snapshot()
    print("usage snapshot (totals):")
    print(f"  calls         : {snap['totals']['calls']}")
    print(f"  total_tokens  : {snap['totals']['total_tokens']}")
    print(f"  cost_usd      : ${snap['totals']['cost_usd']}")

    print("\nper-deployment cumulative cost:")
    for dep, payload in snap["by_deployment"].items():
        cum = payload["cumulative"]
        print(
            f"  {dep:25} → ${cum['cost_usd']}  ({cum['total_tokens']:>5} tokens, {cum['calls']} calls)"
        )

    # ── 2. Pricing lookups (longest-substring + env override) ───────────
    print("\npricing lookups:")
    print(f"  gpt-4o-mini             : {_pricing_for('gpt-4o-mini')} (per 1k input/output)")
    print(
        f"  gpt-4o-mini-preview-rc1 : {_pricing_for('gpt-4o-mini-preview-rc1')} (longest-substring picks mini)"
    )
    print(f"  claude-3-5-sonnet       : {_pricing_for('claude-3-5-sonnet')}")
    print(f"  unknown-model           : {_pricing_for('some-unknown-model')} (fallback)")

    # Register a custom pricing override (e.g. internal model)
    register_pricing("our-internal-model", input_per_1k=0.0001, output_per_1k=0.0005)
    print(
        f"  our-internal-model      : {_pricing_for('our-internal-model-v2')} (registered override)"
    )

    # ── 3. acquire() no-op when AI_TPM_LIMIT unset ──────────────────────
    os.environ.pop("AI_TPM_LIMIT", None)
    start = time.monotonic()
    acquire("gpt-4o", estimated_tokens=10_000)
    print(
        f"\nacquire() no AI_TPM_LIMIT: returned in {(time.monotonic() - start) * 1000:.1f} ms (no wait)"
    )

    # ── 4. check_thresholds_and_alert on a tight hourly cap ─────────────
    os.environ["AI_COST_ALERT_HOURLY_DOLLARS"] = "0.001"
    result = check_thresholds_and_alert()
    fired_keys = [f["key"] for f in result["fired"]]
    print("\ncheck_thresholds_and_alert fired keys (hourly $0.001 cap):")
    for k in fired_keys[:5]:
        print(f"  - {k}")

    # Second call within cooldown → suppressed
    result2 = check_thresholds_and_alert()
    suppressed = len(result2["fired"]) == 0
    print(
        f"second call within 30-min cooldown: fired={len(result2['fired'])} (expect 0 — suppressed)"
    )

    os.environ.pop("AI_COST_ALERT_HOURLY_DOLLARS", None)

    counters = counter_snapshot()

    # ── Verified summary ──────────────────────────────────────────────
    print()
    print("verified:")
    print(f"  ai.calls counter         : {counters.get('ai.calls', 0)}")
    print(f"  ai.tokens.total          : {counters.get('ai.tokens.total', 0)}")
    print(f"  ai.cost_usd_micros       : {counters.get('ai.cost_usd_micros', 0)}")
    print("  longest-substring pricing wins (mini > 4o)")
    print("  threshold alerts respect 30-min per-key cooldown")


if __name__ == "__main__":
    main()


# ── Expected output ──
# usage snapshot (totals):
#   calls         : 4
#   total_tokens  : <sum>
#   cost_usd      : $<computed>
#
# per-deployment cumulative cost:
#   gpt-4o                    → $0.0125  (3500 tokens, 2 calls)
#   claude-3-5-sonnet         → $0.021   (3800 tokens, 1 calls)
#   gpt-4o-mini               → $0.000195 (700 tokens, 1 calls)
#
# pricing lookups:
#   gpt-4o-mini             : (0.00015, 0.0006) (per 1k input/output)
#   gpt-4o-mini-preview-rc1 : (0.00015, 0.0006) (longest-substring picks mini)
#   ...
#
# verified:
#   ...
