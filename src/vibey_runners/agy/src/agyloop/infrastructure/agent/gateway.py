# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""``AgentGateway`` backed by ``google.antigravity.Agent`` + ``LocalAgentConfig``.

Wraps ``Agent(config)`` as an async context manager, drains ``chat()`` inside
try/except, and maps ``Antigravity*Error`` into ``TurnSignals`` for
``classify()``. Vendor types never leave this adapter.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from google.antigravity import Agent, LocalAgentConfig
from google.antigravity.types import (
    AntigravityCancelledError,
    AntigravityConnectionError,
    AntigravityExecutionError,
    AntigravityValidationError,
    ChatResponse,
)

from agyloop.application.dto import TurnOutcome
from agyloop.domain.classify import TurnSignals, looks_like_operator_cancel

try:
    from websockets.exceptions import ConnectionClosed
except ImportError:
    ConnectionClosed = type("ConnectionClosed", (Exception,), {})  # type: ignore[misc,assignment]

from agyloop.domain.errors import AgentConfigError
from agyloop.domain.model_profile import ModelEffortProfile
from agyloop.domain.permission import (
    DEFAULT_USER_PERMISSION_MODE,
    UserPermissionMode,
    parse_user_permission_mode,
)
from agyloop.infrastructure.agent.harness_logs import (
    capture_harness_logs,
    raise_if_empty_withdrawn,
)
from agyloop.infrastructure.agent.harness_retarget import prepare_harness
from agyloop.infrastructure.agent.options import build_local_config
from agyloop.infrastructure.agent.translate import (
    outcome_from_exception,
    partial_text_from_response,
    verdict_from_structured,
)

EventListener = Callable[[dict[str, object]], None]


def _usage_tokens(response: object, kind: str) -> int:
    usage = getattr(response, "usage_metadata", None) or getattr(response, "usage", None)
    if usage is None:
        return 0
    names = {
        "prompt": ("prompt_token_count", "prompt_tokens", "input_tokens"),
        "completion": ("candidates_token_count", "completion_tokens", "output_tokens"),
    }
    for attr in names[kind]:
        value = getattr(usage, attr, None)
        if isinstance(value, int) and value >= 0:
            return value
        if isinstance(usage, dict):
            raw = usage.get(attr)
            if isinstance(raw, int) and raw >= 0:
                return raw
    return 0


class AntigravityAgentGateway:
    """One live Antigravity Agent session. Connect lazily on first send_turn()."""

    def __init__(
        self,
        *,
        cwd: str,
        conversation_id: str | None = None,
        model: str | None = None,
        permission_mode: UserPermissionMode = DEFAULT_USER_PERMISSION_MODE,
        add_dirs: list[str] | None = None,
        system_prompt_append: str = "",
        api_key: str | None = None,
        on_event: EventListener | None = None,
        plan_seed: str | None = None,
        strict_autonomy: bool = False,
    ) -> None:
        self._cwd = cwd
        self._conversation_id = conversation_id
        self._model = model
        self._permission_mode: UserPermissionMode = permission_mode
        self._add_dirs = list(add_dirs or [])
        self._system_prompt_append = system_prompt_append
        self._api_key = api_key
        self._on_event = on_event
        self._plan_seed = plan_seed
        self._strict_autonomy = strict_autonomy
        self._resume_degraded = False
        self._agent: Agent | None = None

    def resolve_tool_approval(self, request_id: str, *, allow: bool, reason: str = "") -> bool:
        del request_id, allow, reason
        return False

    def _config(self) -> LocalAgentConfig:
        return build_local_config(
            cwd=self._cwd,
            conversation_id=self._conversation_id,
            model=self._model,
            permission_mode=self._permission_mode,
            add_dirs=self._add_dirs,
            system_prompt_append=self._system_prompt_append,
            api_key=self._api_key,
            strict_autonomy=self._strict_autonomy,
        )

    async def _reconnect(self) -> None:
        if self._agent is not None:
            await self.close()

    async def set_profile(self, profile: ModelEffortProfile) -> None:
        if self._model == profile.model:
            return
        self._model = profile.model
        await self._reconnect()

    async def set_permission_mode(self, mode: str) -> None:
        parsed = parse_user_permission_mode(mode)
        if parsed == self._permission_mode:
            return
        self._permission_mode = parsed
        await self._reconnect()

    async def set_cwd(self, cwd: str) -> None:
        if cwd == self._cwd:
            return
        self._cwd = cwd
        await self._reconnect()

    async def set_session_resources(self, **kwargs: Any) -> None:
        changed = False
        add_dirs = kwargs.get("add_dirs")
        system_prompt_append = kwargs.get("system_prompt_append")
        if add_dirs is not None and list(add_dirs) != self._add_dirs:
            self._add_dirs = list(add_dirs)
            changed = True
        if (
            system_prompt_append is not None
            and str(system_prompt_append) != self._system_prompt_append
        ):
            self._system_prompt_append = str(system_prompt_append)
            changed = True
        if changed:
            await self._reconnect()

    async def _ensure_started(self) -> Agent:
        if self._agent is not None and not getattr(self._agent, "is_started", True):
            await self.close()
        if self._agent is None:
            prepare_harness()
            agent = Agent(self._config())
            self._agent = await agent.__aenter__()
        return self._agent

    async def send_turn(self, prompt_text: str) -> TurnOutcome:
        response: ChatResponse | None = None
        agent: Agent | None = None
        try:
            agent = await self._ensure_started()
            with capture_harness_logs() as logs:
                response = await agent.chat(prompt_text)
                output_text = await response.text()
            structured = await response.structured_output()
            session_id = agent.conversation_id
            if isinstance(session_id, str) and session_id:
                self._conversation_id = session_id
            raise_if_empty_withdrawn(output_text=output_text, logs=logs)
            signals = TurnSignals()
            if looks_like_operator_cancel(output_text):
                signals = TurnSignals(message=output_text, exception_message=output_text)
            outcome = TurnOutcome(
                signals=signals,
                verdict=verdict_from_structured(structured),
                output_text=output_text,
                session_id=session_id if isinstance(session_id, str) else None,
                prompt_tokens=_usage_tokens(response, "prompt"),
                completion_tokens=_usage_tokens(response, "completion"),
            )
            if self._on_event is not None:
                self._on_event(
                    {
                        "event": "turn_complete",
                        "session_id": outcome.session_id or "",
                        "text_len": len(output_text),
                    }
                )
            return outcome
        except (
            AntigravityValidationError,
            AntigravityCancelledError,
            AntigravityExecutionError,
            AntigravityConnectionError,
            ConnectionClosed,
            ConnectionResetError,
            BrokenPipeError,
            EOFError,
            RuntimeError,
        ) as exc:
            if self._should_degrade_resume(exc):
                self._conversation_id = None
                self._resume_degraded = True
                await self.close()
                return await self.send_turn(self._seeded_prompt(prompt_text))
            if isinstance(exc, (ConnectionClosed, ConnectionResetError, BrokenPipeError, EOFError)):
                exc = AntigravityConnectionError(str(exc))
            if isinstance(exc, AntigravityValidationError):
                raise AgentConfigError(str(exc)) from exc
            if agent is None:
                raise
            partial = partial_text_from_response(response) if response is not None else ""
            session_id = agent.conversation_id
            return outcome_from_exception(
                exc,
                output_text=partial,
                session_id=session_id if isinstance(session_id, str) else None,
            )

    def _should_degrade_resume(self, exc: BaseException) -> bool:
        if not self._conversation_id or self._resume_degraded:
            return False
        text = str(exc).lower()
        return "conversation" in text and any(
            marker in text
            for marker in ("not found", "unknown", "invalid", "expired", "cannot resume")
        )

    def _seeded_prompt(self, prompt_text: str) -> str:
        seed = (self._plan_seed or "").strip()
        if not seed:
            return prompt_text
        return (
            "Previous conversation could not be resumed. Continue from this "
            f"persisted plan state:\n\n{seed}\n\n{prompt_text}"
        )

    async def close(self) -> None:
        if self._agent is not None:
            await self._agent.__aexit__(None, None, None)
            self._agent = None
