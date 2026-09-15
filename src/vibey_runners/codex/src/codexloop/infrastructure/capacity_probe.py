# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Layered capacity probe: app-server (B), rollout (C), exec (A)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from inspect import isawaitable

from codexloop.application.dto import ProbeResult
from codexloop.application.ports import CapacityProbe
from codexloop.domain.capacity import PlanWindows

AppServerLimits = Callable[[], Awaitable[PlanWindows | None] | PlanWindows | None]
RolloutLimits = Callable[[], PlanWindows | None]


class CompositeCapacityProbe:
    """Exec is always authoritative; B and C only enrich the snapshot."""

    def __init__(
        self,
        exec_probe: CapacityProbe,
        *,
        app_server: AppServerLimits | None = None,
        rollout: RolloutLimits | None = None,
    ) -> None:
        self._exec = exec_probe
        self._app_server = app_server
        self._rollout = rollout

    async def probe(self) -> ProbeResult:
        snapshot = await self._read_app_server()
        if snapshot is None:
            snapshot = self._read_rollout()
        exec_result = await self._exec.probe()
        return ProbeResult(outcome=exec_result.outcome, snapshot=snapshot or exec_result.snapshot)

    async def _read_app_server(self) -> PlanWindows | None:
        if self._app_server is None:
            return None
        try:
            result = self._app_server()
            if isawaitable(result):
                return await result
            return result
        except Exception:
            return None

    def _read_rollout(self) -> PlanWindows | None:
        if self._rollout is None:
            return None
        try:
            return self._rollout()
        except Exception:
            return None


__all__ = ["CompositeCapacityProbe"]
