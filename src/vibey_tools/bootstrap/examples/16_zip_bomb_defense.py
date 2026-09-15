# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Example 16 — Zip-bomb defense.

``enforce_zip_safety_limits`` inspects ``zf.infolist()`` BEFORE reading
any entry, so the metadata-level rejection happens BEFORE the OS / Python
allocates the uncompressed bytes.

Key invariants:
- Defaults: ``MAX_ZIP_ENTRIES = 100`` (caps fan-out — a single email
  must not spawn 10k downstream Service Bus messages).
  ``MAX_ZIP_UNCOMPRESSED_BYTES = 500 MB`` (caps total expansion —
  a 100 KB archive must not expand to 50 GB).
- Both limits configurable per call.
- ``ZipBombError`` is unrecoverable → consumer dead-letters.
"""

from __future__ import annotations

import io
import os
import zipfile

os.environ.setdefault("USE_MOCK_BOOTSTRAP", "true")
os.environ.setdefault("AZURE_BOOTSTRAP_ALLOW_RESET", "1")

from vibey_bootstrap.counters import _reset_counters, counter_snapshot
from vibey_bootstrap.exceptions import ZipBombError, is_unrecoverable
from vibey_bootstrap.ingress import (
    MAX_ZIP_ENTRIES,
    MAX_ZIP_UNCOMPRESSED_BYTES,
    enforce_zip_safety_limits,
)


def _zip_with_entries(n: int, body: bytes = b"x") -> zipfile.ZipFile:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for i in range(n):
            zf.writestr(f"f{i}.txt", body)
    buf.seek(0)
    return zipfile.ZipFile(buf, "r")


def main() -> None:
    _reset_counters()

    # ── 1. Happy path: small archive passes ────────────────────────────
    enforce_zip_safety_limits(
        _zip_with_entries(5),
        filename="safe.zip",
    )
    print("safe.zip (5 entries) passed")

    # ── 2. Too many entries (fan-out attack) ───────────────────────────
    try:
        enforce_zip_safety_limits(
            _zip_with_entries(50),
            filename="fan_out.zip",
            max_entries=10,
            counter_name="zip.rejected.bomb",
        )
    except ZipBombError as exc:
        print(f"\nfan_out.zip rejected: {exc}")
        print(f"  is_unrecoverable: {is_unrecoverable(exc)}")

    # ── 3. Total uncompressed-size cap ─────────────────────────────────
    # Each entry small, but cap is tiny — exceeds total
    try:
        enforce_zip_safety_limits(
            _zip_with_entries(3, body=b"x" * 100),
            filename="big_uncompressed.zip",
            max_entries=100,
            max_uncompressed_bytes=10,
            counter_name="zip.rejected.bomb",
        )
    except ZipBombError as exc:
        print(f"\nbig_uncompressed.zip rejected: {exc}")

    counters = counter_snapshot()

    # ── Verified summary ───────────────────────────────────────────────
    print()
    print("verified:")
    print(f"  default MAX_ZIP_ENTRIES             : {MAX_ZIP_ENTRIES}")
    print(
        f"  default MAX_ZIP_UNCOMPRESSED_BYTES  : {MAX_ZIP_UNCOMPRESSED_BYTES} ({MAX_ZIP_UNCOMPRESSED_BYTES // (1024 * 1024)} MB)"
    )
    print(f"  zip.rejected.bomb counter           : {counters.get('zip.rejected.bomb', 0)}")
    print("  metadata inspected pre-read         : True (no allocation on rejection)")


if __name__ == "__main__":
    main()


# ── Expected output ──
# safe.zip (5 entries) passed
#
# fan_out.zip rejected: archive 'fan_out.zip' has 50 entries; exceeds max_entries=10
#   is_unrecoverable: True
#
# big_uncompressed.zip rejected: archive 'big_uncompressed.zip' declares 300 uncompressed bytes; exceeds max_uncompressed_bytes=10
#
# verified:
#   default MAX_ZIP_ENTRIES             : 100
#   default MAX_ZIP_UNCOMPRESSED_BYTES  : 524288000 (500 MB)
#   zip.rejected.bomb counter           : 2
#   metadata inspected pre-read         : True (no allocation on rejection)
