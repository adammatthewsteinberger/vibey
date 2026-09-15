"""Example 14 — Tenacity retry wrappers.

The v2 retry decorators bake in:
- Counter conventions: ``{ns}.runs`` at function entry,
  ``{ns}.calls.{ok|invalid_response|rate_limit_or_http_error|unexpected_error}``
  by outcome.
- ``before_sleep_log(logger, WARNING)`` so each retry attempt is visible
  in logs — silent retry is a debugging nightmare.
- ``reraise=True`` by default — apps that want tenacity's ``RetryError``
  wrapping opt in explicitly.

Requires ``pip install vibey-bootstrap[retry]``.
"""

from __future__ import annotations

import os

os.environ.setdefault("USE_MOCK_BOOTSTRAP", "true")
os.environ.setdefault("AZURE_BOOTSTRAP_ALLOW_RESET", "1")

from vibey_bootstrap.counters import _reset_counters, counter_snapshot
from vibey_bootstrap.exceptions import NetworkError, RateLimitError
from vibey_bootstrap.logging import configure_logging
from vibey_bootstrap.retry import (
    build_retry,
    retry_ai_transient,
    retry_azure_transient,
)

# ── Preset: Azure SDK transient errors (3 attempts, 2–10s) ──────────────
state = {"calls": 0}


@retry_azure_transient(
    operation="example.azure_call",
    counter_namespace="example.azure_call",
    max_attempts=3,
    wait_min_seconds=0.001,
    wait_max_seconds=0.005,
)
def fetch_blob() -> str:
    state["calls"] += 1
    if state["calls"] < 2:
        raise NetworkError("connection reset")
    return "blob-bytes"


# ── Preset: AI rate-limit storms (7 attempts, 2–120s) ───────────────────
ai_state = {"calls": 0}


@retry_ai_transient(
    operation="example.ai_call",
    counter_namespace="example.ai_call",
    max_attempts=4,
    wait_min_seconds=0.001,
    wait_max_seconds=0.005,
)
def call_openai() -> str:
    ai_state["calls"] += 1
    if ai_state["calls"] < 3:
        raise RateLimitError("429 from Azure OpenAI")
    return "completion text"


# ── Custom build_retry with a rate-limit callback ───────────────────────
rate_limit_events: list[BaseException] = []


@build_retry(
    operation="example.custom",
    retry_on=(NetworkError, RateLimitError),
    max_attempts=3,
    wait_min_seconds=0.001,
    wait_max_seconds=0.005,
    counter_namespace="example.custom",
    rate_limit_callback=rate_limit_events.append,
)
def upload_to_sharepoint() -> str:
    if not rate_limit_events:
        raise RateLimitError("first attempt rate-limited")
    return "uploaded"


def main() -> None:
    configure_logging()
    _reset_counters()

    print(f"fetch_blob (transient flake recovers): {fetch_blob()}")
    print(f"call_openai (2× rate-limited, then ok): {call_openai()}")
    print(f"upload_to_sharepoint: {upload_to_sharepoint()}")
    print(f"  rate-limit callback invocations: {len(rate_limit_events)}")

    counters = counter_snapshot()

    # ── Verified summary ───────────────────────────────────────────────
    print()
    print("verified:")
    print(
        f"  azure_call.runs           : {counters['example.azure_call.runs']} (one entry per outer call)"
    )
    print(f"  azure_call.calls.ok       : {counters['example.azure_call.calls.ok']}")
    print(f"  ai_call.runs              : {counters['example.ai_call.runs']}")
    print(f"  ai_call.calls.ok          : {counters['example.ai_call.calls.ok']}")
    print(f"  custom.calls.ok           : {counters['example.custom.calls.ok']}")
    print("  before_sleep_log fired WARNING lines for each retry sleep")


if __name__ == "__main__":
    main()


# ── Expected output ──
# <WARNING log lines for each retry sleep>
# fetch_blob (transient flake recovers): blob-bytes
# call_openai (2× rate-limited, then ok): completion text
# upload_to_sharepoint: uploaded
#   rate-limit callback invocations: 1
#
# verified:
#   azure_call.runs           : 1 (one entry per outer call)
#   azure_call.calls.ok       : 1
#   ai_call.runs              : 1
#   ai_call.calls.ok          : 1
#   custom.calls.ok           : 1
#   before_sleep_log fired WARNING lines for each retry sleep
