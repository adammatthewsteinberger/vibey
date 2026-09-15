# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Per-turn stall watchdog. Cancels a run that stops emitting or overruns.

Cursor exposes no ask-user interception point, so a model that parks on a
question (or otherwise never terminates) is survivable only because this
watchdog calls ``run.cancel()`` — guarded by ``run.status == "running"``,
because cancel on an already-terminal run raises UnsupportedRunOperationError.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from cursorloop.application.ports import Clock

_RUNNING = "running"


class TurnWatchdog:
    """Cancels a stalled or over-budget run. tick() is the only async entry."""

    def __init__(
        self,
        turn_timeout: timedelta,
        stall_timeout: timedelta,
        clock: Clock,
    ) -> None:
        self._turn_timeout = turn_timeout
        self._stall_timeout = stall_timeout
        self._clock = clock
        self._run: object | None = None
        self._turn_started_at: datetime | None = None
        self._last_delta_at: datetime | None = None

    def turn_started(self, run: object) -> None:
        now = self._clock.now()
        self._run = run
        self._turn_started_at = now
        self._last_delta_at = now

    def saw_delta(self) -> None:
        self._last_delta_at = self._clock.now()

    async def tick(self) -> None:
        run = self._run
        if run is None or getattr(run, "status", None) != _RUNNING:
            return
        now = self._clock.now()
        if self._turn_started_at is not None and now - self._turn_started_at >= self._turn_timeout:
            self._cancel(run)
            return
        if self._last_delta_at is not None and now - self._last_delta_at >= self._stall_timeout:
            self._cancel(run)

    def _cancel(self, run: object) -> None:
        if getattr(run, "status", None) != _RUNNING:
            return
        cancel = getattr(run, "cancel", None)
        if callable(cancel):
            cancel()
