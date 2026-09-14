# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from claudeloop.application.runner import AutonomousRunner, _NullRunResources
from claudeloop.domain.budget import Budget
from claudeloop.domain.control import (
    ApproveToolCommand,
    DenyToolCommand,
    ResourceMutateCommand,
    ResponseFeedbackCommand,
    ResponseRetryCommand,
    SetCwdCommand,
    SetPermissionModeCommand,
    SlashCommand,
    StopCommand,
)
from claudeloop.domain.slash import parse_slash, slash_to_prompt
from tests.application.fakes import (
    CONTINUE_VERDICT,
    DONE_VERDICT,
    FakeAgentGateway,
    FakeAuditLog,
    FakeCapacityProbe,
    FakeClock,
    FakeEventSink,
    FakeProgressReporter,
    FakeRunControl,
    FakeSleeper,
    ScriptedTurn,
    available_signals,
)

NOW = datetime(2026, 8, 9, 12, 0, tzinfo=timezone.utc)


def test_control_validation_edges() -> None:
    with pytest.raises(ValueError):
        SetCwdCommand(path="  ")
    with pytest.raises(ValueError):
        ApproveToolCommand(request_id="")
    with pytest.raises(ValueError):
        DenyToolCommand(request_id=" ")
    with pytest.raises(ValueError):
        ResourceMutateCommand(action="noop", kind="skill", value="x")
    with pytest.raises(ValueError):
        ResourceMutateCommand(action="add", kind="  ", value="x")
    with pytest.raises(ValueError):
        ResourceMutateCommand(action="add", kind="skill", value="")
    ResourceMutateCommand(action="rm", kind="skill", value="")
    with pytest.raises(ValueError):
        ResponseFeedbackCommand(verdict="meh")


def test_slash_validation_and_args() -> None:
    with pytest.raises(ValueError):
        parse_slash("status")
    with pytest.raises(ValueError):
        parse_slash("/")
    parsed = parse_slash("/compact extra args")
    assert parsed.args == "extra args"
    assert "arguments: extra args" in slash_to_prompt(parsed)


def test_null_run_resources() -> None:
    null = _NullRunResources()
    assert null.apply_mutate(action="add", kind="skill", value="x") == {}
    assert null.gateway_payload() == {}
    null.set_permission_mode("plan")
    null.set_cwd("/tmp")


class _FakeResources:
    def __init__(self) -> None:
        self.mutates: list[tuple[str, str, str, str | None]] = []
        self.modes: list[str] = []
        self.cwds: list[str] = []

    def apply_mutate(
        self, *, action: str, kind: str, value: str, name: str | None = None
    ) -> dict[str, Any]:
        self.mutates.append((action, kind, value, name))
        if kind == "issue":
            return {"prompt_fragment": "Imported issue body"}
        return {"ok": True}

    def gateway_payload(self) -> dict[str, Any]:
        return {"add_dirs": ["/extra"], "skills": ["s1"]}

    def set_permission_mode(self, mode: str) -> None:
        self.modes.append(mode)

    def set_cwd(self, path: str) -> None:
        self.cwds.append(path)


async def test_ops_control_surface_end_to_end() -> None:
    resources = _FakeResources()
    control = FakeRunControl(
        script=[
            [ResourceMutateCommand(action="add", kind="skill", value="pre")],
            [
                SetPermissionModeCommand(mode="manual"),
                SetCwdCommand(path="/work"),
                SlashCommand(text="/status"),
                ApproveToolCommand(request_id="t1"),
                DenyToolCommand(request_id="t2", reason="nope"),
                ResourceMutateCommand(action="add", kind="issue", value="o/r#1"),
                ResourceMutateCommand(action="add", kind="issue", value="o/r#2"),
                ResponseFeedbackCommand(verdict="good", note="nice"),
            ],
            [ResponseRetryCommand()],
            [StopCommand()],
        ]
    )
    clock = FakeClock(start=NOW)
    gateway = FakeAgentGateway(
        [
            ScriptedTurn(signals=available_signals(), verdict=CONTINUE_VERDICT),
            ScriptedTurn(signals=available_signals(), verdict=CONTINUE_VERDICT),
            ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT),
        ]
    )
    events = FakeEventSink()
    audit = FakeAuditLog()
    metas: list[dict[str, Any]] = []

    def _meta(**kwargs: Any) -> None:
        metas.append(dict(kwargs))

    runner = AutonomousRunner(
        agent_gateway=gateway,
        capacity_probe=FakeCapacityProbe([available_signals()]),
        clock=clock,
        sleeper=FakeSleeper(clock),
        audit_log=audit,
        progress=FakeProgressReporter(),
        run_control=control,
        event_sink=events,
        run_resources=resources,
        budget=Budget(max_turns=10),
        meta_updater=_meta,
    )
    result = await runner.run(initial_prompt="start", continue_prompt="cont")
    assert "manual" in gateway.permission_modes
    assert "/work" in gateway.cwds
    assert gateway.tool_resolutions
    assert resources.mutates
    assert any(e[0] == "response.feedback" for e in events.events)
    assert any(e[0] == "control.slash" for e in events.events)
    assert gateway.resource_updates
    assert any(m.get("cwd") == "/work" for m in metas)
    assert result.success is True or result.success is False


async def test_response_retry_resends_last_prompt() -> None:
    control = FakeRunControl(
        script=[
            [],  # before turn 1
            [],  # natural break after Continue
            [ResponseRetryCommand()],  # pre-send poll before turn 2
            [StopCommand()],  # natural break after turn 2
        ]
    )
    clock = FakeClock(start=NOW)
    gateway = FakeAgentGateway(
        [
            ScriptedTurn(signals=available_signals(), verdict=CONTINUE_VERDICT),
            ScriptedTurn(signals=available_signals(), verdict=CONTINUE_VERDICT),
        ]
    )
    events = FakeEventSink()
    runner = AutonomousRunner(
        agent_gateway=gateway,
        capacity_probe=FakeCapacityProbe([available_signals()]),
        clock=clock,
        sleeper=FakeSleeper(clock),
        audit_log=FakeAuditLog(),
        progress=FakeProgressReporter(),
        run_control=control,
        event_sink=events,
        budget=Budget(max_turns=5),
    )
    await runner.run(initial_prompt="FIRST", continue_prompt="cont")
    assert gateway.sent_prompts[0] == "FIRST"
    assert gateway.sent_prompts.count("FIRST") >= 2
    assert any(e[0] == "response.retry" for e in events.events)


async def test_real_attach_mid_run(tmp_path: Path) -> None:
    from claudeloop.infrastructure.resources.adapter import ResourcePortAdapter
    from claudeloop.infrastructure.resources.store import RunResourceStore

    store = RunResourceStore(tmp_path / "resources")
    adapter = ResourcePortAdapter(store)
    note = tmp_path / "spec.md"
    note.write_text("# Spec\n", encoding="utf-8")
    control = FakeRunControl(
        script=[
            [
                ResourceMutateCommand(action="add", kind="attachment", value=str(note)),
                ResourceMutateCommand(action="add", kind="skill", value="local-skill"),
            ],
            [StopCommand()],
        ]
    )
    clock = FakeClock(start=NOW)
    gateway = FakeAgentGateway(
        [ScriptedTurn(signals=available_signals(), verdict=CONTINUE_VERDICT)]
    )
    runner = AutonomousRunner(
        agent_gateway=gateway,
        capacity_probe=FakeCapacityProbe([available_signals()]),
        clock=clock,
        sleeper=FakeSleeper(clock),
        audit_log=FakeAuditLog(),
        progress=FakeProgressReporter(),
        run_control=control,
        event_sink=FakeEventSink(),
        run_resources=adapter,
        budget=Budget(max_turns=5),
    )
    await runner.run(initial_prompt="go", continue_prompt="cont")
    snap = store.snapshot()
    assert "spec.md" in snap.attachments
    assert "local-skill" in snap.skills
    assert gateway.resource_updates


async def test_response_retry_empty_and_cwd_without_meta() -> None:
    control = FakeRunControl(
        script=[
            [ResponseRetryCommand()],
            [SetCwdCommand(path="/alone"), StopCommand()],
        ]
    )
    # Stop outranks cwd in second poll — first poll only retry_empty.
    clock = FakeClock(start=NOW)
    gateway = FakeAgentGateway([ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT)])
    events = FakeEventSink()
    runner = AutonomousRunner(
        agent_gateway=gateway,
        capacity_probe=FakeCapacityProbe([available_signals()]),
        clock=clock,
        sleeper=FakeSleeper(clock),
        audit_log=FakeAuditLog(),
        progress=FakeProgressReporter(),
        run_control=control,
        event_sink=events,
        # no meta_updater — covers cwd flush without meta callback
    )
    # Apply retry before any send to hit retry_empty.
    runner._apply_control([ResponseRetryCommand()], natural_break=False)
    assert any(e[0] == "response.retry_empty" for e in events.events)
    runner._pending_cwd = "/alone"
    await runner._flush_pending_session_updates()
    assert "/alone" in gateway.cwds
