# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Pure exponential backoff with injected jitter."""

from __future__ import annotations

import math
from collections.abc import Callable
from datetime import timedelta


def backoff(
    attempt: int,
    *,
    base: timedelta,
    ceiling: timedelta,
    jitter_ratio: float,
    rand: Callable[[], float],
) -> timedelta:
    """Return ``min(ceiling, base * 2^attempt)`` scaled by jitter from ``rand``.

    ``rand`` must return a float in ``[0, 1]``. Jitter maps that onto
    ``[1 - jitter_ratio, 1 + jitter_ratio]``. The result is never negative and
    never exceeds ``ceiling``.
    """
    ceiling_s = max(ceiling.total_seconds(), 0.0)
    base_s = max(base.total_seconds(), 0.0)
    try:
        exponential = math.ldexp(base_s, attempt)
    except (OverflowError, ValueError):
        exponential = math.inf
    delay_s = min(ceiling_s, exponential)
    factor = (1.0 - jitter_ratio) + (2.0 * jitter_ratio * rand())
    jittered = delay_s * factor
    clamped = min(max(jittered, 0.0), ceiling_s)
    return timedelta(seconds=clamped)
