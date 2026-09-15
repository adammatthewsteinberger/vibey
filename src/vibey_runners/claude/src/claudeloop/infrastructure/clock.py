# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Real Clock and Sleeper adapters. FakeClock/FakeSleeper for tests live in
tests/application/fakes.py — never here, so production code never imports
test doubles."""

from __future__ import annotations

from datetime import datetime, timezone

import anyio


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)


class AnyioSleeper:
    """Sleeps in real wall-clock time via anyio, so it works under both the
    asyncio and trio backends the CLI's async bridge may select."""

    def __init__(self, clock: SystemClock) -> None:
        self._clock = clock

    async def sleep_until(self, instant: datetime) -> None:
        delay = (instant - self._clock.now()).total_seconds()
        if delay > 0:
            await anyio.sleep(delay)
