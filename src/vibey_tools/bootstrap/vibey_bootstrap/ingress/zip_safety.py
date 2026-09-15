# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Zip-bomb defense. Inspect ``infolist`` metadata BEFORE reading any entry."""

from __future__ import annotations

import zipfile

from vibey_bootstrap.counters import bump_counter
from vibey_bootstrap.exceptions import ZipBombError

MAX_ZIP_ENTRIES = 100
MAX_ZIP_UNCOMPRESSED_BYTES = 500 * 1024 * 1024


def enforce_zip_safety_limits(
    zf: zipfile.ZipFile,
    *,
    filename: str,
    max_entries: int = MAX_ZIP_ENTRIES,
    max_uncompressed_bytes: int = MAX_ZIP_UNCOMPRESSED_BYTES,
    counter_name: str | None = None,
) -> None:
    """Raise :class:`ZipBombError` when the archive metadata exceeds limits.

    Inspects ``zf.infolist()`` only — does NOT call ``zf.read()`` (which
    would allocate the uncompressed bytes). The whole point is to gate on
    the declared metadata BEFORE any expansion.
    """
    infos = zf.infolist()
    if len(infos) > max_entries:
        if counter_name:
            bump_counter(counter_name)
        raise ZipBombError(
            f"archive {filename!r} has {len(infos)} entries; exceeds max_entries={max_entries}"
        )
    total = sum(info.file_size for info in infos)
    if total > max_uncompressed_bytes:
        if counter_name:
            bump_counter(counter_name)
        raise ZipBombError(
            f"archive {filename!r} declares {total} uncompressed bytes; "
            f"exceeds max_uncompressed_bytes={max_uncompressed_bytes}"
        )


__all__ = [
    "MAX_ZIP_ENTRIES",
    "MAX_ZIP_UNCOMPRESSED_BYTES",
    "enforce_zip_safety_limits",
]
