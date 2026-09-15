"""Block-scoped diagnostic timer.

For *inside* a function that's already ``@traced``. Does not record into the
latency histogram — use ``@traced`` for that.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any


@contextmanager
def timed_operation(
    logger: logging.Logger, operation: str, **extra: Any
) -> Generator[dict[str, Any], None, None]:
    """Time a block; emit a DEBUG log on exit if the logger is enabled for DEBUG."""
    fields: dict[str, Any] = dict(extra)
    start = time.monotonic()
    try:
        yield fields
    finally:
        elapsed = round(time.monotonic() - start, 3)
        if logger.isEnabledFor(logging.DEBUG):
            payload = {**fields, "operation": operation, "elapsed_seconds": elapsed}
            logger.debug("⏱ %s in %.3fs", operation, elapsed, extra=payload)
