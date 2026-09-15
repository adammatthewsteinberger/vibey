# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Durable Cursor Agent gateway: one send_turn maps to one agent.send() → Run.

Per-run model overrides are sticky. The gateway re-asserts the active profile
on every send (and again after the turn) so a one-off escalation cannot
silently bill every later turn at the higher rate.

``cursor_sdk`` stays in this package. ``CursorAgentError`` (and duck-typed
lookalikes) become ``TurnSignals`` via ``signals_from_exception``.
"""

from __future__ import annotations

import contextlib
from dataclasses import replace
from typing import Any

import anyio
from cursor_sdk import LocalSendOptions, SendOptions

from cursorloop.application.dto import TurnOutcome
from cursorloop.application.ports import RunEventSink
from cursorloop.domain.model_profile import ModelProfile
from cursorloop.domain.session import runtime_from_id
from cursorloop.infrastructure.agent.options import _model_selection
from cursorloop.infrastructure.agent.translate import (
    TeeStream,
    outcome_from_run,
    signals_from_exception,
)
from cursorloop.infrastructure.agent.watchdog import TurnWatchdog

_RUNNING = "running"
_WATCH_INTERVAL_SECONDS = 0.05


def _is_cursor_agent_error(exc: BaseException) -> bool:
    return any(cls.__name__ == "CursorAgentError" for cls in type(exc).__mro__)


class CursorAgentGateway:
    """Wraps a durable ``cursor_sdk.Agent``. An errored Run does not invalidate it."""

    def __init__(
        self,
        client: Any,
        agent: Any,
        profile: ModelProfile,
        watchdog: TurnWatchdog,
        event_sink: RunEventSink,
    ) -> None:
        self._client = client
        self._agent = agent
        self._profile = profile
        self._watchdog = watchdog
        self._event_sink = event_sink
        self._active_run: object | None = None
        self._cwd: str | None = None
        self._reassert_profile()

    def agent_id(self) -> str:
        value = getattr(self._agent, "agent_id", "") or ""
        return value if isinstance(value, str) else str(value)

    async def set_profile(self, profile: ModelProfile) -> None:
        self._profile = profile
        self._reassert_profile()

    async def set_cwd(self, cwd: str) -> None:
        self._cwd = cwd

    async def close(self) -> None:
        closer = getattr(self._agent, "close", None)
        if callable(closer):
            # Bridge may have already disposed the agent (or the live process
            # already tore it down after a capacity error).
            with contextlib.suppress(Exception):
                closer()

    async def cancel_active_run(self) -> bool:
        run = self._active_run
        if run is None or getattr(run, "status", None) != _RUNNING:
            return False
        cancel = getattr(run, "cancel", None)
        if not callable(cancel):
            return False
        cancel()
        return True

    async def send_turn(self, prompt_text: str, *, force: bool = False) -> TurnOutcome:
        options = self._send_options(force=force)
        try:
            run = self._agent.send(prompt_text, options)
            self._active_run = run
            self._watchdog.turn_started(run)
            tee = TeeStream(run, sink=self._event_sink, turn_id=str(getattr(run, "id", "") or ""))
            buffered = await self._drain_while_watching(run, tee)
            outcome = outcome_from_run(
                run,
                buffered,
                signals_fallback=tee.status_error_text,
            )
            return replace(outcome, raw_events=tuple(tee.raw_events))
        except Exception as exc:
            if _is_cursor_agent_error(exc):
                return TurnOutcome(
                    signals=signals_from_exception(exc),
                    verdict=None,
                    output_text="",
                    agent_id=self.agent_id(),
                    cost_usd=None,
                    cost_pending=True,
                )
            raise
        finally:
            self._reassert_profile()

    async def _drain_while_watching(self, run: object, tee: TeeStream) -> str:
        """Tick the watchdog while drain blocks in another thread.

        A hung ``messages()``/``wait()`` must not freeze ticks: stall/turn
        timeout has to call ``run.cancel()`` on a still-running handle.
        """

        async def watch() -> None:
            while getattr(run, "status", None) == _RUNNING:
                await self._watchdog.tick()
                if getattr(run, "status", None) != _RUNNING:
                    return
                await anyio.sleep(_WATCH_INTERVAL_SECONDS)

        buffered = ""
        async with anyio.create_task_group() as tg:
            tg.start_soon(watch)
            try:
                buffered = await anyio.to_thread.run_sync(tee.drain)
            finally:
                tg.cancel_scope.cancel()
        return buffered

    def _send_options(self, *, force: bool) -> SendOptions:
        local: LocalSendOptions | None = None
        if runtime_from_id(self.agent_id()) == "local":
            local = LocalSendOptions(force=force)
        return SendOptions(
            model=_model_selection(self._profile),
            local=local,
            on_delta=self._on_delta,
        )

    def _on_delta(self, _update: object) -> None:
        self._watchdog.saw_delta()

    def _reassert_profile(self) -> None:
        if hasattr(self._agent, "model"):
            self._agent.model = _model_selection(self._profile)
