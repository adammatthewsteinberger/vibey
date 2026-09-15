"""Example 07 — Local settings + USE_MOCK_BOOTSTRAP.

Demonstrates the Azure-Functions-style ``local.settings.json`` loader and
the ``USE_MOCK_BOOTSTRAP`` env-var that short-circuits real Azure calls
during local development.

Key invariants:
- ``load_local_settings`` NEVER overrides an existing ``os.environ`` entry.
  Real env wins; local file fills the gaps.
- Keys starting with ``_`` are documentation sentinels and are skipped.
- Missing file is silent (returns 0). Malformed JSON is logged WARN and
  returns 0 — no exception escapes.
- ``USE_MOCK_BOOTSTRAP=true`` makes ``ensure_bootstrap()`` set the
  initialized flag without contacting Azure App Config / Key Vault.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

os.environ.setdefault("USE_MOCK_BOOTSTRAP", "true")

from vibey_bootstrap.bootstrap import (
    bootstrap_initialized,
    ensure_bootstrap,
    load_local_settings,
)


def main() -> None:
    # ── 1. Mimic an Azure Functions local.settings.json ────────────────
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "local.settings.json"
        path.write_text(
            json.dumps(
                {
                    "IsEncrypted": False,
                    "Values": {
                        "_COMMENT_FOO": "this should be skipped",
                        "EXAMPLE_DB_HOST": "localhost",
                        "EXAMPLE_FEATURE_FLAG": "on",
                        "EXAMPLE_PRESERVED": "from-file",
                    },
                }
            )
        )

        # Pre-set one env var to demonstrate "real env wins"
        os.environ["EXAMPLE_PRESERVED"] = "from-real-env"
        os.environ.pop("EXAMPLE_DB_HOST", None)
        os.environ.pop("EXAMPLE_FEATURE_FLAG", None)
        os.environ.pop("_COMMENT_FOO", None)

        loaded = load_local_settings(path)

    # ── 2. Bootstrap with mock mode — no Azure connections ─────────────
    ensure_bootstrap()
    ensure_bootstrap()  # idempotent

    # ── Verified summary ───────────────────────────────────────────────
    print()
    print("verified:")
    print(f"  keys loaded from file        : {loaded}")
    print(f"  EXAMPLE_DB_HOST              : {os.environ.get('EXAMPLE_DB_HOST')!r}")
    print(f"  EXAMPLE_FEATURE_FLAG         : {os.environ.get('EXAMPLE_FEATURE_FLAG')!r}")
    print(f"  EXAMPLE_PRESERVED (real wins): {os.environ.get('EXAMPLE_PRESERVED')!r}")
    print(f"  _COMMENT_FOO skipped         : {'_COMMENT_FOO' not in os.environ}")
    print(f"  bootstrap_initialized()      : {bootstrap_initialized()}")
    print(f"  load missing file (silent)   : {load_local_settings('/tmp/nonexistent.json')}")


if __name__ == "__main__":
    # Clean up env after run so this example can be sourced repeatedly.
    try:
        main()
    finally:
        for k in ("EXAMPLE_DB_HOST", "EXAMPLE_FEATURE_FLAG", "EXAMPLE_PRESERVED"):
            os.environ.pop(k, None)


# ── Expected output ──
# verified:
#   keys loaded from file        : 2
#   EXAMPLE_DB_HOST              : 'localhost'
#   EXAMPLE_FEATURE_FLAG         : 'on'
#   EXAMPLE_PRESERVED (real wins): 'from-real-env'
#   _COMMENT_FOO skipped         : True
#   bootstrap_initialized()      : True
#   load missing file (silent)   : 0
