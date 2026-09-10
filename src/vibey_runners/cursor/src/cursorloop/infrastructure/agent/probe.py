# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Throwaway capacity probe: create/send/drain/dispose with no tools.

``tools=[]`` offers no built-in tools — the model can only respond with text.
``setting_sources=None`` is hermetic. We stream-drain the throwaway Run so a
status ``ERROR`` message (e.g. "You're out of usage") reaches the classifier;
``Agent.prompt().wait()`` alone leaves ``result`` empty on those paths.
"""

from __future__ import annotations

import contextlib
from collections.abc import Callable
from typing import Any

import anyio
from cursor_sdk import Agent, AgentOptions

from cursorloop.application.dto import TurnOutcome
from cursorloop.domain.model_profile import SHIPPED_PRESETS, ModelProfile
from cursorloop.infrastructure.agent.options import build_agent_options
from cursorloop.infrastructure.agent.translate import (
    TeeStream,
    outcome_from_run,
    signals_from_exception,
)

_PROBE_NAME = "cursorloop-probe"
_PROBE_PROMPT = "ok"


def build_probe_options(
    *,
    cwd: str,
    profile: ModelProfile | None = None,
) -> AgentOptions:
    """Pure-ish builder so probe options are testable without a live client.

    ``auto_review`` stays False and ``mode`` stays ``"agent"`` because
    ``build_agent_options`` hard-defaults both. Grok ``effort`` survives on
    ModelSelection params because that builder is the only mapping site.
    """
    return build_agent_options(
        profile=profile if profile is not None else SHIPPED_PRESETS["composer"],
        cwd=cwd,
        tools=[],
        name=_PROBE_NAME,
        setting_sources=None,
    )


def _is_cursor_agent_error(exc: BaseException) -> bool:
    return any(cls.__name__ == "CursorAgentError" for cls in type(exc).__mro__)


def _default_prompt(message: object, options: object, **kwargs: object) -> object:
    """Legacy injectables for unit tests — prefer the streamed path in production."""
    return Agent.prompt(message, options, **kwargs)  # type: ignore[arg-type]


class CursorCapacityProbe:
    """Cheap throwaway capacity check via a no-tools create/send/drain."""

    def __init__(
        self,
        cwd: str,
        profile: ModelProfile,
        *,
        prompt: Callable[..., object] | None = None,
        client: Any | None = None,
        create_agent: Callable[..., Any] | None = None,
        use_streamed_probe: bool | None = None,
    ) -> None:
        self._cwd = cwd
        self._profile = profile
        self._prompt = prompt if prompt is not None else _default_prompt
        self._client = client
        self._create_agent = create_agent if create_agent is not None else Agent.create
        # Injected ``prompt`` keeps the old Agent.prompt shape for unit tests;
        # live/bootstrap omit it so we stream-drain status ERROR copy.
        if use_streamed_probe is None:
            use_streamed_probe = prompt is None
        self._use_streamed_probe = use_streamed_probe

    async def probe(self) -> TurnOutcome:
        options = build_probe_options(cwd=self._cwd, profile=self._profile)
        try:
            if self._use_streamed_probe:
                return await self._probe_streamed(options)
            result = self._prompt(_PROBE_PROMPT, options)
        except Exception as exc:
            if _is_cursor_agent_error(exc):
                return TurnOutcome(
                    signals=signals_from_exception(exc),
                    verdict=None,
                    output_text="",
                    cost_usd=None,
                    cost_pending=True,
                )
            raise
        text = getattr(result, "result", None)
        buffered = text if isinstance(text, str) else ""
        return outcome_from_run(result, buffered)

    async def _probe_streamed(self, options: AgentOptions) -> TurnOutcome:
        create_kwargs: dict[str, Any] = {"options": options}
        if self._client is not None:
            create_kwargs["client"] = self._client
        agent = self._create_agent(**create_kwargs)
        try:
            send = getattr(agent, "send", None)
            if not callable(send):
                raise RuntimeError("probe agent has no send()")
            run = send(_PROBE_PROMPT)
            tee = TeeStream(run)
            buffered = await anyio.to_thread.run_sync(tee.drain)
            return outcome_from_run(
                run,
                buffered,
                signals_fallback=tee.status_error_text,
            )
        except Exception as exc:
            if _is_cursor_agent_error(exc):
                return TurnOutcome(
                    signals=signals_from_exception(exc),
                    verdict=None,
                    output_text="",
                    cost_usd=None,
                    cost_pending=True,
                )
            raise
        finally:
            closer = getattr(agent, "close", None)
            if callable(closer):
                with contextlib.suppress(Exception):
                    closer()
