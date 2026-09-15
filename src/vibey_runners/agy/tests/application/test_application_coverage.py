# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from agyloop.application.dto import TurnOutcome
from agyloop.application.runner import AutonomousRunner
from agyloop.application.usecases.doctor import (
    AuthResolution,
    HarnessStatus,
    run_doctor,
)
from agyloop.application.usecases.run_control import (
    request_prompt,
    request_resource_mutate,
    request_response_feedback,
    request_response_retry,
    request_set_cwd,
    request_set_effort,
    request_set_model,
    request_set_permission_mode,
    request_set_preset,
    request_slash,
    request_stop,
    request_tool_decision,
)
from agyloop.domain.budget import Budget
from agyloop.domain.classify import TurnSignals
from agyloop.domain.control import (
    ApproveToolCommand,
    DenyToolCommand,
    PromptDeferredCommand,
    PromptNowCommand,
    ResourceMutateCommand,
    ResponseFeedbackCommand,
    ResponseRetryCommand,
    SetCwdCommand,
    SetEffortCommand,
    SetModelCommand,
    SetPermissionModeCommand,
    SetPresetCommand,
    SlashCommand,
    StopCommand,
)
from agyloop.domain.waiting import WaitPolicyConfig


class _FakeInbox:
    def __init__(self) -> None:
        self.commands: list[object] = []

    def enqueue(self, command: object) -> None:
        self.commands.append(command)


def test_all_run_control_usecases() -> None:
    inbox = _FakeInbox()

    res = request_stop(inbox, run_id="r1")
    assert res.command_type == "stop"
    assert inbox.commands[-1] == StopCommand()

    res = request_prompt(inbox, "now", immediate=True, run_id="r1")
    assert res.command_type == "prompt_now"
    assert inbox.commands[-1] == PromptNowCommand(text="now")

    res = request_prompt(inbox, "later", immediate=False, run_id="r1")
    assert res.command_type == "prompt_deferred"
    assert inbox.commands[-1] == PromptDeferredCommand(text="later")

    res = request_set_model(inbox, "gemini-3-pro", run_id="r1")
    assert res.command_type == "set_model"
    assert inbox.commands[-1] == SetModelCommand(model="gemini-3-pro")

    res = request_set_effort(inbox, "high", run_id="r1")
    assert res.command_type == "set_effort"
    assert inbox.commands[-1] == SetEffortCommand(effort="high")

    res = request_set_preset(inbox, "high", run_id="r1")
    assert res.command_type == "set_preset"
    assert inbox.commands[-1] == SetPresetCommand(preset="high")

    res = request_set_permission_mode(inbox, "yolo", run_id="r1")
    assert res.command_type == "set_permission_mode"
    assert inbox.commands[-1] == SetPermissionModeCommand(mode="yolo")

    res = request_set_cwd(inbox, "/tmp/dir", run_id="r1")
    assert res.command_type == "set_cwd"
    assert inbox.commands[-1] == SetCwdCommand(path="/tmp/dir")

    res = request_slash(inbox, "/compact", run_id="r1")
    assert res.command_type == "slash"
    assert inbox.commands[-1] == SlashCommand(text="/compact")

    res = request_tool_decision(inbox, "req1", allow=True, run_id="r1")
    assert res.command_type == "approve_tool"
    assert inbox.commands[-1] == ApproveToolCommand(request_id="req1")

    res = request_tool_decision(inbox, "req2", allow=False, reason="custom reason", run_id="r1")
    assert res.command_type == "deny_tool"
    assert inbox.commands[-1] == DenyToolCommand(request_id="req2", reason="custom reason")

    res = request_tool_decision(inbox, "req3", allow=False, run_id="r1")
    assert res.command_type == "deny_tool"
    assert inbox.commands[-1] == DenyToolCommand(request_id="req3", reason="denied by operator")

    res = request_resource_mutate(
        inbox, action="add", kind="skill", value="foo", name="bar", run_id="r1"
    )
    assert res.command_type == "resource_mutate"
    assert inbox.commands[-1] == ResourceMutateCommand(
        action="add", kind="skill", value="foo", name="bar"
    )

    res = request_response_feedback(inbox, verdict="good", note="great", run_id="r1")
    assert res.command_type == "response_feedback"
    assert inbox.commands[-1] == ResponseFeedbackCommand(verdict="good", note="great")

    res = request_response_retry(inbox, run_id="r1")
    assert res.command_type == "response_retry"
    assert inbox.commands[-1] == ResponseRetryCommand()


class _DoctorEnvWithCli:
    def __init__(self, cli_path: str | None, cli_version: str | None) -> None:
        self._cli_path = cli_path
        self._cli_version = cli_version

    def resolve_auth(self) -> AuthResolution:
        return AuthResolution(
            lane="developer_api", source="GOOGLE_API_KEY", authenticated=True, detail="ok"
        )

    def interactive_hooks_registered(self) -> bool:
        return False

    def find_agy_cli(self) -> str | None:
        return self._cli_path

    def agy_cli_version(self, path: str) -> str | None:
        return self._cli_version

    def configured_mcp_servers(self) -> list[str]:
        return []

    def check_sdk_harness(self) -> HarnessStatus:
        return HarnessStatus(available=True, detail="stock harness available")


def test_doctor_with_cli_found(tmp_path: Path) -> None:
    env = _DoctorEnvWithCli(cli_path="/bin/agy", cli_version="0.1.0")
    checks = run_doctor(env, cwd=tmp_path)
    cli_check = next(c for c in checks if c.name == "agy-cli")
    assert "0.1.0" in cli_check.detail

    env2 = _DoctorEnvWithCli(cli_path="/bin/agy", cli_version=None)
    checks2 = run_doctor(env2, cwd=tmp_path)
    cli_check2 = next(c for c in checks2 if c.name == "agy-cli")
    assert "version unknown" in cli_check2.detail


def test_runner_no_probe_flag_replaces_wait_policy() -> None:
    gateway = AsyncMock()
    probe = AsyncMock()
    clock = MagicMock()
    sleeper = AsyncMock()
    audit = MagicMock()
    progress = MagicMock()

    runner = AutonomousRunner(
        agent_gateway=gateway,
        capacity_probe=probe,
        clock=clock,
        sleeper=sleeper,
        audit_log=audit,
        progress=progress,
        budget=Budget(),
        wait_policy=WaitPolicyConfig(no_probe=False),
        no_probe=True,
    )
    assert runner._wait_policy.no_probe is True


@pytest.mark.asyncio
async def test_runner_turn_with_exception_signals(tmp_path: Path) -> None:
    gateway = AsyncMock()
    gateway.send_turn.return_value = TurnOutcome(
        signals=TurnSignals(exception_type="ResourceExhausted", exception_message="Quota hit"),
        verdict=None,
        output_text="done AGYLOOP_TASK_FULLY_COMPLETE",
        session_id="s1",
    )
    probe = AsyncMock()
    clock = MagicMock()
    clock.now.return_value = datetime(2026, 8, 13, tzinfo=UTC)
    sleeper = AsyncMock()
    audit = MagicMock()
    progress = MagicMock()
    events = MagicMock()

    runner = AutonomousRunner(
        agent_gateway=gateway,
        capacity_probe=probe,
        clock=clock,
        sleeper=sleeper,
        audit_log=audit,
        progress=progress,
        event_sink=events,
        budget=Budget(max_turns=1),
        wait_policy=WaitPolicyConfig(no_probe=True),
        no_probe=True,
    )

    result = await runner.run(initial_prompt="go", continue_prompt="continue")
    assert result.success is True
    # Verify event emitted with exception_type
    calls = [call for call in events.emit.call_args_list if call[0][0] == "turn.completed"]
    assert len(calls) == 1
    assert calls[0][0][1]["exception_type"] == "ResourceExhausted"
    assert "Quota hit" in calls[0][0][1]["exception_message"]


@pytest.mark.asyncio
async def test_runner_stops_during_quota_wait() -> None:
    from tests.application.fakes import (
        FakeAgentGateway,
        FakeAuditLog,
        FakeClock,
        FakeProgressReporter,
        FakeRunControl,
        FakeSleeper,
        ScriptedTurn,
        rpm_window_signals,
    )

    now = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)
    clock = FakeClock(now)
    sleeper = FakeSleeper(clock)
    gateway = FakeAgentGateway([ScriptedTurn(signals=rpm_window_signals())])
    probe = AsyncMock()
    audit = FakeAuditLog()
    progress = FakeProgressReporter()
    control = FakeRunControl([[], [], [StopCommand()]])

    runner = AutonomousRunner(
        agent_gateway=gateway,
        capacity_probe=probe,
        clock=clock,
        sleeper=sleeper,
        audit_log=audit,
        progress=progress,
        run_control=control,
        budget=Budget(max_turns=2),
        wait_policy=WaitPolicyConfig(no_probe=True),
        no_probe=True,
    )

    result = await runner.run(initial_prompt="go", continue_prompt="continue")
    assert result.success is False
    assert "stopped by operator" in result.reason
