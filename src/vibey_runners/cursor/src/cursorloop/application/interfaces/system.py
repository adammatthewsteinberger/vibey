# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Time and sleeping -- the two ambient effects the run loop needs faked."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable


@runtime_checkable
class Clock(Protocol):
    """Current instant as an aware datetime."""

    def now(self) -> datetime: ...


@runtime_checkable
class Sleeper(Protocol):
    """Wait until the given instant. Must not require a human."""

    async def sleep_until(self, instant: datetime) -> None: ...
