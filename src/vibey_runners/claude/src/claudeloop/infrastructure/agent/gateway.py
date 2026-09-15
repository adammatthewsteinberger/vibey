# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""ClaudeSDKClient-backed AgentGateway and CapacityProbe.

Deliberately uses ClaudeSDKClient (streaming-input mode), never query() —
query() raises a bare Exception after yielding an error ResultMessage and the
process exits non-zero, where ClaudeSDKClient survives to be resumed with
another send_turn(). See
docs/architecture/decisions/0002-agent-sdk-over-subprocess.md."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Literal

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient
from structlog.stdlib import BoundLogger

from claudeloop.application.dto import TurnOutcome
from claudeloop.domain.model_profile import ModelEffortProfile
from claudeloop.domain.permission import (
    DEFAULT_USER_PERMISSION_MODE,
    UserPermissionMode,
    parse_user_permission_mode,
)
from claudeloop.infrastructure.agent.options import build_probe_options, build_turn_options
from claudeloop.infrastructure.agent.translate import TurnAccumulator
from claudeloop.infrastructure.logging import get_logger
from claudeloop.infrastructure.tool_approval import ToolApprovalGate

EventListener = Callable[[dict[str, object]], None]


def _logger() -> BoundLogger:
    return get_logger(component="agent.gateway")


class ClaudeAgentGateway:
    """One live ClaudeSDKClient session. Connect lazily on first send_turn()
    so constructing the gateway never itself talks to the SDK."""

    def __init__(
        self,
        *,
        cwd: str,
        session_id: str | None = None,
        resume: str | None = None,
        continue_conversation: bool = False,
        max_turns: int | None = None,
        max_budget_usd: float | None = None,
        retry_watchdog: bool = False,
        model: str | None = None,
        effort: str | None = None,
        on_event: EventListener | None = None,
        max_buffer_size: int | None = None,
        include_partial_messages: bool = False,
        permission_mode: UserPermissionMode = DEFAULT_USER_PERMISSION_MODE,
        add_dirs: list[str] | None = None,
        skills: list[str] | Literal["all"] | None = None,
        plugins: list[str] | None = None,
        mcp_servers: dict[str, Any] | None = None,
        system_prompt_append: str = "",
        allowed_tools: list[str] | None = None,
        tool_approval_timeout: float = 30.0,
    ) -> None:
        self._cwd = cwd
        self._session_id = session_id
        self._resume = resume
        self._continue_conversation = continue_conversation
        self._max_turns = max_turns
        self._max_budget_usd = max_budget_usd
        self._retry_watchdog = retry_watchdog
        self._model = model
        self._effort = effort
        self._on_event = on_event
        self._max_buffer_size = max_buffer_size
        self._include_partial_messages = include_partial_messages
        self._permission_mode: UserPermissionMode = permission_mode
        self._add_dirs = list(add_dirs or [])
        self._skills = skills
        self._plugins = list(plugins or [])
        self._mcp_servers = dict(mcp_servers or {})
        self._system_prompt_append = system_prompt_append
        self._allowed_tools = list(allowed_tools or [])
        self._approval = ToolApprovalGate(timeout_seconds=tool_approval_timeout)
        self._client: ClaudeSDKClient | None = None
        self._delta_seq = 0

    def set_event_listener(self, on_event: EventListener | None) -> None:
        self._on_event = on_event

    def resolve_tool_approval(self, request_id: str, *, allow: bool, reason: str = "") -> bool:
        return self._approval.resolve(request_id, allow=allow, reason=reason)

    def _options(self) -> ClaudeAgentOptions:
        return build_turn_options(
            cwd=self._cwd,
            session_id=self._session_id,
            resume=self._resume,
            continue_conversation=self._continue_conversation,
            max_turns=self._max_turns,
            max_budget_usd=self._max_budget_usd,
            retry_watchdog=self._retry_watchdog,
            model=self._model,
            effort=self._effort,
            max_buffer_size=self._max_buffer_size,
            include_partial_messages=self._include_partial_messages,
            permission_mode=self._permission_mode,
            add_dirs=self._add_dirs,
            skills=self._skills,
            plugins=self._plugins,
            mcp_servers=self._mcp_servers or None,
            can_use_tool=self._approval.can_use_tool,
            system_prompt_append=self._system_prompt_append,
            allowed_tools=self._allowed_tools or None,
        )

    async def _reconnect(self) -> None:
        if self._client is not None:
            await self.close()
            # Prefer resume=<known id> over continue_conversation: the latter
            # is "most recent in cwd", and pairing continue with session_id
            # is rejected by the CLI without fork_session.
            if self._session_id:
                self._resume = self._session_id
                self._continue_conversation = False
            else:
                self._continue_conversation = True

    async def set_profile(self, profile: ModelEffortProfile) -> None:
        if self._model == profile.model and self._effort == profile.effort:
            return
        _logger().info(
            "model.profile_changed",
            model=profile.model,
            effort=profile.effort,
            preset=profile.preset,
        )
        self._model = profile.model
        self._effort = profile.effort
        await self._reconnect()

    async def set_permission_mode(self, mode: str) -> None:
        parsed = parse_user_permission_mode(mode)
        if parsed == self._permission_mode:
            return
        _logger().info(
            "permission.mode_changed",
            from_mode=self._permission_mode,
            to_mode=parsed,
        )
        self._permission_mode = parsed
        await self._reconnect()

    async def set_cwd(self, cwd: str) -> None:
        if cwd == self._cwd:
            return
        _logger().info("cwd.changed", cwd=cwd)
        self._cwd = cwd
        await self._reconnect()

    async def set_session_resources(self, **kwargs: Any) -> None:
        add_dirs = kwargs.get("add_dirs")
        skills = kwargs.get("skills")
        plugins = kwargs.get("plugins")
        mcp_servers = kwargs.get("mcp_servers")
        system_prompt_append = kwargs.get("system_prompt_append")
        allowed_tools = kwargs.get("allowed_tools")
        changed = False
        if add_dirs is not None and list(add_dirs) != self._add_dirs:
            self._add_dirs = list(add_dirs)
            changed = True
        if skills is not None and skills != self._skills:
            self._skills = skills
            changed = True
        if plugins is not None and list(plugins) != self._plugins:
            self._plugins = list(plugins)
            changed = True
        if mcp_servers is not None and dict(mcp_servers) != self._mcp_servers:
            self._mcp_servers = dict(mcp_servers)
            changed = True
        if system_prompt_append is not None and system_prompt_append != self._system_prompt_append:
            self._system_prompt_append = str(system_prompt_append)
            changed = True
        if allowed_tools is not None and list(allowed_tools) != self._allowed_tools:
            self._allowed_tools = list(allowed_tools)
            changed = True
        if changed:
            _logger().info(
                "session.resources_changed",
                add_dirs=len(self._add_dirs),
                skills=self._skills,
                plugins=len(self._plugins),
                mcp=len(self._mcp_servers),
            )
            await self._reconnect()

    async def _ensure_connected(self) -> ClaudeSDKClient:
        # Flush approval-needed events from the gate into the listener.
        for event in self._approval.drain_events():
            if self._on_event is not None:
                self._on_event(event)
        if self._client is None:
            _logger().info(
                "gateway.connect",
                cwd=self._cwd,
                model=self._model,
                effort=self._effort,
                permission_mode=self._permission_mode,
                max_buffer_size=self._max_buffer_size,
                resume=bool(self._resume),
                continue_conversation=self._continue_conversation,
                include_partial_messages=self._include_partial_messages,
            )
            self._client = ClaudeSDKClient(options=self._options())
            await self._client.connect()
            # First send is a fresh/resumed session; subsequent sends continue
            # the same live connection — resume/continue_conversation should
            # not be re-applied on turn two or the SDK would treat it as a
            # second resume request.
            self._resume = None
            self._continue_conversation = False
        return self._client

    async def send_turn(self, prompt_text: str) -> TurnOutcome:
        _logger().info("gateway.send_turn.start", prompt_len=len(prompt_text))
        client = await self._ensure_connected()

        def _on_event(event: dict[str, object]) -> None:
            if event.get("type") == "StreamEvent":
                delta = event.get("delta_text")
                if isinstance(delta, str) and delta:
                    self._delta_seq += 1
                    enriched = {
                        **event,
                        "chatter": "delta",
                        "seq": self._delta_seq,
                    }
                    if self._on_event is not None:
                        self._on_event(enriched)
                    return
            if self._on_event is not None:
                self._on_event(event)

        await client.query(prompt_text)
        accumulator = TurnAccumulator(on_event=_on_event)
        async for message in client.receive_response():
            for event in self._approval.drain_events():
                if self._on_event is not None:
                    self._on_event(event)
            accumulator.feed(message)
            _logger().debug("gateway.sdk_message", message_type=type(message).__name__)
        outcome = accumulator.build()
        _logger().info(
            "gateway.send_turn.done",
            session_id=outcome.session_id,
            cost_usd=outcome.cost_usd,
            output_len=len(outcome.output_text),
        )
        if outcome.session_id:
            self._session_id = outcome.session_id
        return outcome

    async def close(self) -> None:
        if self._client is not None:
            _logger().info("gateway.close")
            await self._client.disconnect()
            self._client = None


class ClaudeCapacityProbe:
    """A one-token, tool-free, transcript-free turn used purely to re-check
    capacity while WAITING. Opens and closes its own throwaway client per
    probe so it never pollutes the main session transcript."""

    def __init__(
        self,
        *,
        cwd: str,
        on_event: EventListener | None = None,
        max_buffer_size: int | None = None,
        model: str | None = None,
    ) -> None:
        self._cwd = cwd
        self._on_event = on_event
        self._max_buffer_size = max_buffer_size
        self._model = model

    def set_model(self, model: str | None) -> None:
        """Keep the probe on the same model as the live run."""
        self._model = model

    async def probe(self) -> TurnOutcome:
        options = build_probe_options(
            cwd=self._cwd,
            max_buffer_size=self._max_buffer_size,
            model=self._model,
        )
        _logger().info("gateway.probe.start", model=self._model)
        client = ClaudeSDKClient(options=options)
        await client.connect()
        try:
            await client.query("Reply with the single word OK and nothing else.")
            accumulator = TurnAccumulator(on_event=self._on_event)
            async for message in client.receive_response():
                accumulator.feed(message)
            outcome = accumulator.build()
            _logger().info("gateway.probe.done", cost_usd=outcome.cost_usd)
            return outcome
        finally:
            await client.disconnect()
