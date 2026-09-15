# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Parse HTTP Retry-After header values into absolute datetimes."""

from __future__ import annotations

import math
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime


def parse_retry_after(value: str | None, *, now: datetime) -> datetime | None:
    """Parse a Retry-After value as integer seconds or an HTTP-date.

    Never raises. Blank or unparseable input returns ``None``. Parsed instants
    before ``now`` are clamped to ``now`` so a wait policy never busy-spins.
    """
    if value is None:
        return None

    stripped = value.strip()
    if not stripped:
        return None

    try:
        seconds = float(stripped)
    except ValueError:
        pass
    else:
        if seconds < 0:
            return now
        if not math.isfinite(seconds):
            return None
        try:
            return now + timedelta(seconds=seconds)
        except OverflowError:
            return None

    try:
        parsed = parsedate_to_datetime(stripped)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=now.tzinfo)
        elif now.tzinfo is None:
            return None
        if parsed < now:
            return now
        return parsed
    except (TypeError, ValueError, OverflowError):
        return None
