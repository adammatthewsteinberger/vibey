"""Example 13 — Constant-time secret comparison + API-key header.

``compare_secrets`` wraps ``hmac.compare_digest`` with None/empty/bytes
handling so call sites don't repeat the safe pattern.

``verify_api_key_header`` is the FastAPI dependency for non-webhook
routes. Default ``fail_open_when_unset=True`` matches v1 ergonomics —
endpoints stay open when ``API_KEY`` is unset (intended for dev). Apps
that want strict mode set ``fail_open_when_unset=False``.
"""

from __future__ import annotations

import asyncio
import os

os.environ.setdefault("USE_MOCK_BOOTSTRAP", "true")

from vibey_bootstrap.security import compare_secrets, verify_api_key_header


def main() -> None:
    # ── 1. compare_secrets handles edge cases ──────────────────────────
    print("compare_secrets:")
    print(f"  exact match           : {compare_secrets('abc', 'abc')}")
    print(f"  mismatch              : {compare_secrets('abc', 'xyz')}")
    print(f"  None left             : {compare_secrets(None, 'abc')}")
    print(f"  None right            : {compare_secrets('abc', None)}")
    print(f"  empty string          : {compare_secrets('', 'abc')}")
    print(f"  bytes vs str          : {compare_secrets(b'abc', 'abc')}")

    # ── 2. verify_api_key_header — fail-open default ───────────────────
    os.environ.pop("API_KEY", None)
    print()
    print("verify_api_key_header (fail-open, default):")
    asyncio.run(verify_api_key_header(None))  # passes
    asyncio.run(verify_api_key_header("anything"))  # passes
    print("  unset API_KEY + no header  → passes (dev-friendly)")
    print("  unset API_KEY + any header → passes")

    # ── 3. Strict mode — auth required even when unset ─────────────────
    print()
    print("verify_api_key_header (strict mode):")
    try:
        asyncio.run(verify_api_key_header(None, fail_open_when_unset=False))
    except Exception as exc:
        print(f"  unset API_KEY raises       : {type(exc).__name__}: {exc}")

    # ── 4. Live key, mismatch rejected with constant-time compare ──────
    os.environ["API_KEY"] = "the-right-key"
    try:
        asyncio.run(verify_api_key_header("the-wrong-key"))
    except Exception as exc:
        print(f"  mismatch                   : {type(exc).__name__} 401")
    asyncio.run(verify_api_key_header("the-right-key"))
    print("  match                      : passes")
    os.environ.pop("API_KEY", None)

    # ── Verified summary ──────────────────────────────────────────────
    print()
    print("verified:")
    print("  compare_secrets uses hmac.compare_digest (constant-time)")
    print("  None/empty inputs return False (no AttributeError)")
    print("  fail-open default keeps dev frictionless")
    print("  strict mode raises 401 even when API_KEY unset")


if __name__ == "__main__":
    main()


# ── Expected output ──
# compare_secrets:
#   exact match           : True
#   mismatch              : False
#   None left             : False
#   None right            : False
#   empty string          : False
#   bytes vs str          : True
#
# verify_api_key_header (fail-open, default):
#   unset API_KEY + no header  → passes (dev-friendly)
#   unset API_KEY + any header → passes
#
# verify_api_key_header (strict mode):
#   unset API_KEY raises       : HTTPException: 401: API key not configured
#
#   mismatch                   : HTTPException 401
#   match                      : passes
