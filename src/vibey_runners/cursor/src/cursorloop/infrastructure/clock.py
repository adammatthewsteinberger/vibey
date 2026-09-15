# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Real Clock and Sleeper adapters. Test doubles live under tests/, never here."""

from __future__ import annotations

from datetime import UTC, datetime

import anyio


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


class AnyioSleeper:
    """Sleeps in real wall-clock time via anyio (asyncio or trio backends)."""

    def __init__(self, clock: SystemClock) -> None:
        self._clock = clock

    async def sleep_until(self, instant: datetime) -> None:
        delay = (instant - self._clock.now()).total_seconds()
        if delay > 0:
            await anyio.sleep(delay)
