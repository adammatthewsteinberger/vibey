# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Size-cap gate. Raises ``OversizedAttachmentError`` over the cap."""

from __future__ import annotations

from vibey_bootstrap.counters import bump_counter
from vibey_bootstrap.exceptions import OversizedAttachmentError

DEFAULT_MAX_PDF_BYTES = 150 * 1024 * 1024
DEFAULT_MAX_ZIP_UNCOMPRESSED_BYTES = 500 * 1024 * 1024


def enforce_size_cap(
    *,
    size_bytes: int,
    cap_bytes: int,
    filename: str,
    counter_name: str | None = None,
) -> None:
    """Raise :class:`OversizedAttachmentError` when ``size_bytes > cap_bytes``."""
    if size_bytes > cap_bytes:
        if counter_name:
            bump_counter(counter_name)
        raise OversizedAttachmentError(
            f"attachment {filename!r} is {size_bytes} bytes; exceeds cap of {cap_bytes} bytes"
        )


__all__ = [
    "DEFAULT_MAX_PDF_BYTES",
    "DEFAULT_MAX_ZIP_UNCOMPRESSED_BYTES",
    "enforce_size_cap",
]
