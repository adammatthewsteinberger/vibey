"""Example 03 — Correlation scope.

Demonstrates propagating correlation context across nested sync calls and
async tasks. The ``CorrelationFilter`` installed by ``configure_logging``
auto-attaches every set context var to every LogRecord, so callers don't
have to pass correlation IDs through ``extra={}`` by hand.

Key invariants:
- ``correlation_scope()`` always yields a non-empty string (generates a
  fresh 12-char UUID hex when caller passes None).
- Nested scopes are restored cleanly on exit via ``contextvars.Token``.
- Arbitrary kwargs (e.g. ``email_id``, ``tenant_id``) become context vars
  that propagate the same way.
"""

from __future__ import annotations

import asyncio
import logging
import os

os.environ.setdefault("USE_MOCK_BOOTSTRAP", "true")

from vibey_bootstrap.logging import (
    configure_logging,
    correlation_scope,
    get_correlation_id,
)

logger = logging.getLogger(__name__)


def inner_work() -> str | None:
    """Reads the current correlation id without it being passed in explicitly."""
    cid = get_correlation_id()
    logger.info("inner_work observed correlation_id", extra={"step": "inner"})
    return cid


async def async_step(name: str) -> str | None:
    cid = get_correlation_id()
    logger.info(f"async_step {name}", extra={"step": name})
    return cid


def main() -> None:
    configure_logging()

    # ── 1. Auto-generated correlation id ────────────────────────────────
    with correlation_scope() as cid_outer:
        observed = inner_work()
        assert observed == cid_outer, "inner work must see outer correlation id"

    # ── 2. Explicit id + arbitrary extra fields ────────────────────────
    with correlation_scope("req-abc-123", email_id="msg-99", tenant_id="acme"):
        logger.info("Top-level handler", extra={"phase": "process"})

        # Nested scope replaces correlation id; outer values restored on exit
        with correlation_scope("req-nested-456"):
            assert get_correlation_id() == "req-nested-456"
            logger.info("Nested call", extra={"phase": "subop"})

        assert get_correlation_id() == "req-abc-123"

    # ── 3. Async — same machinery, no extra plumbing ────────────────────
    async def runner() -> tuple[str | None, str | None]:
        with correlation_scope("async-req-777") as cid:
            a = await async_step("first")
            b = await async_step("second")
            assert a == cid and b == cid
            return a, b

    a, b = asyncio.run(runner())

    # ── Verified summary ──────────────────────────────────────────────
    print()
    print("verified:")
    print(f"  auto-generated cid length    : {len(cid_outer)} (expect 12)")
    print(f"  inner observed outer cid     : {observed == cid_outer}")
    print(f"  async cid stable across awaits: {a == b == 'async-req-777'}")
    print(f"  outside any scope, cid is    : {get_correlation_id()!r}")


if __name__ == "__main__":
    main()


# ── Expected output ──
# <log lines auto-tagged with correlation_id + email_id + tenant_id>
#
# verified:
#   auto-generated cid length    : 12 (expect 12)
#   inner observed outer cid     : True
#   async cid stable across awaits: True
#   outside any scope, cid is    : None
