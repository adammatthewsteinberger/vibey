# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any

import anyio
import pytest

from cursorloop.application.ports import AgentGateway
from cursorloop.domain.model_profile import SHIPPED_PRESETS
from cursorloop.domain.session import runtime_from_id
from cursorloop.infrastructure.agent.catalog import CursorAgentCatalog
from cursorloop.infrastructure.agent.gateway import CursorAgentGateway
from cursorloop.infrastructure.agent.watchdog import TurnWatchdog
from tests.application import fakes
from tests.fixtures import sdk_payloads


class FakeRunEventSink:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, Any] | None]] = []

    def emit(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        self.events.append((event_type, payload))

    def bind(
        self,
        *,
        agent_id: str | None = None,
        attempt: int | None = None,
        phase: str | None = None,
        trace_id: str | None = None,
        turn_id: str | None = None,
    ) -> None:
        del agent_id, attempt, phase, trace_id, turn_id


class FakeCursorAgent:
    """Durable Agent double. send() records options and returns a scripted Run."""

    def __init__(
        self,
        *,
        agent_id: str = "agent-1",
        run: object | None = None,
        send_error: BaseException | None = None,
    ) -> None:
        self.agent_id = agent_id
        self.model: object | None = None
        self.closed = False
        self.send_calls: list[tuple[object, object]] = []
        self._run = run if run is not None else sdk_payloads.fake_streaming_run(["hello"])
        self._send_error = send_error

    def send(self, message: object, options: object = None, **kwargs: object) -> object:
        del kwargs
        self.send_calls.append((message, options))
        model = getattr(options, "model", None) if options is not None else None
        if model is not None:
            self.model = model
        if self._send_error is not None:
            raise self._send_error
        on_delta = getattr(options, "on_delta", None) if options is not None else None
        if callable(on_delta):
            on_delta(object())
        return self._run

    def close(self) -> None:
        self.closed = True


def _gateway(
    agent: FakeCursorAgent,
    *,
    profile: object = None,
    watchdog: TurnWatchdog | None = None,
) -> CursorAgentGateway:
    clock = fakes.FakeClock()
    wd = watchdog or TurnWatchdog(
        turn_timeout=timedelta(minutes=30), stall_timeout=timedelta(minutes=10), clock=clock
    )
    return CursorAgentGateway(
        client=object(),
        agent=agent,
        profile=profile if profile is not None else SHIPPED_PRESETS["composer"],
        watchdog=wd,
        event_sink=FakeRunEventSink(),
    )


def test_gateway_structurally_satisfies_the_port() -> None:
    gateway = _gateway(FakeCursorAgent())
    assert isinstance(gateway, AgentGateway)


async def test_send_turn_tees_the_stream_and_returns_an_outcome() -> None:
    agent = FakeCursorAgent(run=sdk_payloads.fake_streaming_run(["hello ", "world"]))
    gateway = _gateway(agent)
    outcome = await gateway.send_turn("do work")
    assert outcome.output_text == "hello world"
    assert outcome.signals.run_status == "finished"
    assert outcome.agent_id == "agent_1"
    assert outcome.raw_events == ()


async def test_force_send_builds_local_send_options() -> None:
    agent = FakeCursorAgent(agent_id="agent-local-1")
    gateway = _gateway(agent)
    await gateway.send_turn("continue", force=True)
    _message, options = agent.send_calls[-1]
    assert options.local is not None
    assert options.local.force is True


async def test_unforced_local_send_still_sets_local_force_false() -> None:
    agent = FakeCursorAgent(agent_id="agent-local-1")
    gateway = _gateway(agent)
    await gateway.send_turn("hello")
    _message, options = agent.send_calls[-1]
    assert options.local is not None
    assert options.local.force is False


async def test_cloud_send_does_not_attach_local_force() -> None:
    agent = FakeCursorAgent(agent_id="bc-cloud-1")
    gateway = _gateway(agent)
    await gateway.send_turn("hello", force=True)
    _message, options = agent.send_calls[-1]
    assert options.local is None
    assert runtime_from_id(agent.agent_id) == "cloud"


async def test_cursor_agent_error_becomes_turn_signals() -> None:
    exc = sdk_payloads.fake_rate_limit_error(
        code="rate_limited", is_retryable=True, retry_after="60", status_code=429
    )
    agent = FakeCursorAgent(send_error=exc)
    gateway = _gateway(agent)
    outcome = await gateway.send_turn("hello")
    assert outcome.signals.error_type == "RateLimitError"
    assert outcome.signals.error_code == "rate_limited"
    assert outcome.signals.http_status == 429
    assert outcome.signals.retry_after == "60"
    assert outcome.verdict is None


async def test_profile_is_reasserted_after_a_one_off_escalation() -> None:
    """Per-run model overrides are sticky. After a one-off escalation the
    gateway must send the restored profile explicitly or every later turn
    silently bills at the higher rate."""
    agent = FakeCursorAgent()
    gateway = _gateway(agent, profile=SHIPPED_PRESETS["composer"])
    await gateway.set_profile(SHIPPED_PRESETS["grok-xhigh"])
    await gateway.send_turn("hard problem")
    await gateway.set_profile(SHIPPED_PRESETS["composer"])
    await gateway.send_turn("continue")
    first_model = agent.send_calls[0][1].model
    second_model = agent.send_calls[1][1].model
    assert first_model.id == "cursor-grok-4.6"
    assert [(p.id, p.value) for p in first_model.params] == [("effort", "xhigh")]
    assert second_model.id == "composer-2.5"
    assert agent.model is not None
    assert agent.model.id == "composer-2.5"


async def test_every_send_reasserts_the_active_profile() -> None:
    agent = FakeCursorAgent()
    gateway = _gateway(agent, profile=SHIPPED_PRESETS["grok"])
    await gateway.send_turn("one")
    await gateway.send_turn("two")
    for _message, options in agent.send_calls:
        assert options.model.id == "cursor-grok-4.6"
        assert [(p.id, p.value) for p in options.model.params] == [("effort", "high")]


async def test_close_set_cwd_cancel_and_agent_id() -> None:
    run = fakes.FakeRun(status="running")
    agent = FakeCursorAgent(agent_id="agent-42", run=run)
    gateway = _gateway(agent)
    assert gateway.agent_id() == "agent-42"
    await gateway.set_cwd("/repo")
    await gateway.send_turn("go")
    assert await gateway.cancel_active_run() is True
    assert run.cancel_calls == 1
    await gateway.close()
    assert agent.closed is True


async def test_cancel_active_run_is_false_when_nothing_is_running() -> None:
    agent = FakeCursorAgent(run=sdk_payloads.fake_run(status="finished", result="done"))
    gateway = _gateway(agent)
    assert await gateway.cancel_active_run() is False
    await gateway.send_turn("go")
    assert await gateway.cancel_active_run() is False


def test_watchdog_cancels_a_stalled_in_flight_stream() -> None:
    """A model that stops emitting holds messages() forever. The watchdog must
    tick while drain is in flight so cancel unblocks send_turn — Cursor has no
    ask-user tool, so this is the stall path that must stay survivable."""
    clock = fakes.FakeClock()
    run = fakes.FakeRun(status="running", block_until_cancel=True)
    watchdog = TurnWatchdog(
        turn_timeout=timedelta(hours=2), stall_timeout=timedelta(minutes=10), clock=clock
    )
    gateway = CursorAgentGateway(
        client=object(),
        agent=FakeCursorAgent(run=run),
        profile=SHIPPED_PRESETS["composer"],
        watchdog=watchdog,
        event_sink=FakeRunEventSink(),
    )
    holder: list[object] = []

    def runner() -> None:
        holder.append(anyio.run(gateway.send_turn, "go"))

    thread = threading.Thread(target=runner)
    thread.start()
    try:
        assert run.block_entered.wait(timeout=2)
        clock.advance(timedelta(minutes=11))
        thread.join(timeout=2)
        assert run.cancel_calls == 1
        assert thread.is_alive() is False
        assert holder
    finally:
        run.cancel()
        thread.join(timeout=1)


async def test_raw_events_from_the_tee_land_on_the_outcome() -> None:
    run = sdk_payloads.fake_run(
        status="finished",
        result="done",
        messages=(sdk_payloads.fake_tool_call_message(name="read"),),
    )
    agent = FakeCursorAgent(run=run)
    gateway = _gateway(agent)
    outcome = await gateway.send_turn("go")
    assert outcome.raw_events
    assert outcome.raw_events[0]["type"] == "tool_call"
    assert outcome.raw_events[0]["name"] == "read"


async def test_unexpected_exceptions_propagate() -> None:
    agent = FakeCursorAgent(send_error=RuntimeError("boom"))
    gateway = _gateway(agent)
    with pytest.raises(RuntimeError, match="boom"):
        await gateway.send_turn("go")


@dataclass
class FakeAgentInfo:
    agent_id: str
    cwd: str
    name: str = "demo"
    summary: str = "working"
    last_modified: str | None = "2026-08-13T12:00:00+00:00"
    status: str = "finished"
    runtime: str | None = None


@dataclass
class FakeAgentsNamespace:
    items: list[FakeAgentInfo]
    list_calls: list[dict[str, Any]] = field(default_factory=list)
    get_calls: list[dict[str, Any]] = field(default_factory=list)
    list_runs_calls: list[dict[str, Any]] = field(default_factory=list)

    def list(self, runtime: str | None = None, cwd: str | None = None, **kwargs: object) -> object:
        self.list_calls.append({"runtime": runtime, "cwd": cwd, **kwargs})
        return SimpleNamespace(items=list(self.items))

    def get(self, agent_id: str, cwd: str | None = None, **kwargs: object) -> FakeAgentInfo:
        del kwargs
        self.get_calls.append({"agent_id": agent_id, "cwd": cwd})
        for item in self.items:
            if item.agent_id == agent_id:
                return item
        raise KeyError(agent_id)

    def list_runs(self, agent_id: str, cwd: str | None = None, **kwargs: object) -> object:
        del kwargs
        self.list_runs_calls.append({"agent_id": agent_id, "cwd": cwd})
        return SimpleNamespace(items=[])


@dataclass
class FakeCatalogClient:
    agents: FakeAgentsNamespace


def test_local_list_and_get_always_pass_cwd() -> None:
    info = FakeAgentInfo(agent_id="agent-1", cwd="/repo")
    client = FakeCatalogClient(agents=FakeAgentsNamespace(items=[info]))
    catalog = CursorAgentCatalog(client)
    listed = catalog.list_all(cwd="/repo")
    assert listed[0].agent_id == "agent-1"
    assert listed[0].cwd == "/repo"
    assert client.agents.list_calls == [{"runtime": "local", "cwd": "/repo"}]
    recent = catalog.most_recent("/repo")
    assert recent is not None
    assert recent.agent_id == "agent-1"
    got = catalog.get("agent-1", cwd="/repo")
    assert got.agent_id == "agent-1"
    assert client.agents.get_calls == [{"agent_id": "agent-1", "cwd": "/repo"}]
    catalog.list_runs("agent-1", cwd="/repo")
    assert client.agents.list_runs_calls == [{"agent_id": "agent-1", "cwd": "/repo"}]


def test_resume_refuses_mismatched_cwd_without_allow_cwd_change() -> None:
    info = FakeAgentInfo(agent_id="agent-1", cwd="/original")
    catalog = CursorAgentCatalog(FakeCatalogClient(agents=FakeAgentsNamespace(items=[info])))
    with pytest.raises(ValueError, match="cwd"):
        catalog.get("agent-1", cwd="/other")
    allowed = catalog.get("agent-1", cwd="/other", allow_cwd_change=True)
    assert allowed.cwd == "/original"


def test_most_recent_returns_none_when_the_directory_has_no_agents() -> None:
    catalog = CursorAgentCatalog(FakeCatalogClient(agents=FakeAgentsNamespace(items=[])))
    assert catalog.most_recent("/repo") is None


def test_most_recent_picks_the_latest_modified_agent() -> None:
    older = FakeAgentInfo(
        agent_id="agent-old", cwd="/repo", last_modified="2026-08-01T00:00:00+00:00"
    )
    newer = FakeAgentInfo(
        agent_id="agent-new", cwd="/repo", last_modified="2026-08-13T12:00:00+00:00"
    )
    catalog = CursorAgentCatalog(
        FakeCatalogClient(agents=FakeAgentsNamespace(items=[older, newer]))
    )
    recent = catalog.most_recent("/repo")
    assert recent is not None
    assert recent.agent_id == "agent-new"
    assert recent.last_modified == datetime(2026, 8, 13, 12, 0, tzinfo=UTC)


def test_bridge_launch_passes_workspace() -> None:
    launches: list[str | None] = []

    class _Launcher:
        @staticmethod
        def launch_bridge(*, workspace: str | None = None, **kwargs: object) -> FakeCatalogClient:
            del kwargs
            launches.append(workspace)
            return FakeCatalogClient(agents=FakeAgentsNamespace(items=[]))

    catalog = CursorAgentCatalog.connect(workspace="/repo", launch_bridge=_Launcher.launch_bridge)
    assert launches == ["/repo"]
    assert catalog.list_all(cwd="/repo") == []


def test_list_all_without_cwd_does_not_force_local_runtime() -> None:
    info = FakeAgentInfo(agent_id="bc-1", cwd="/cloud", runtime="cloud", last_modified="not-a-date")
    client = FakeCatalogClient(agents=FakeAgentsNamespace(items=[info]))
    catalog = CursorAgentCatalog(client)
    listed = catalog.list_all()
    assert client.agents.list_calls == [{"runtime": None, "cwd": None}]
    assert listed[0].runtime == "cloud"
    assert listed[0].last_modified is None
    catalog.list_runs("bc-1")
    assert client.agents.list_runs_calls == [{"agent_id": "bc-1", "cwd": None}]
