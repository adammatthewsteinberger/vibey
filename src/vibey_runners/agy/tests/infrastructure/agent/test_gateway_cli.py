# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""CLI gateway: argv from build_agy_argv, subprocess mocked, 429s classified."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from agyloop.domain.capacity import WindowExhausted
from agyloop.domain.classify import classify
from agyloop.domain.errors import AgentConfigError, UnsafeSkipPermissionsError
from agyloop.infrastructure.agent.cli_argv import AgyCliInvocation
from agyloop.infrastructure.agent.gateway_cli import AgyCliAgentGateway


class _ScriptedAgy:
    def __init__(self, results: list[subprocess.CompletedProcess[str]]) -> None:
        self.results = list(results)
        self.invocations: list[AgyCliInvocation] = []

    def __call__(
        self, invocation: AgyCliInvocation, *, cwd: Path
    ) -> subprocess.CompletedProcess[str]:
        del cwd
        self.invocations.append(invocation)
        return self.results.pop(0)


@pytest.mark.asyncio
async def test_cli_gateway_default_sandbox_argv(tmp_path: Path) -> None:
    scripted = _ScriptedAgy(
        [subprocess.CompletedProcess(args=["agy"], returncode=0, stdout="ok", stderr="")]
    )
    gateway = AgyCliAgentGateway(
        cwd=str(tmp_path),
        conversation_id="conv-1",
        model="gemini-2.5-pro",
        runner=scripted,
    )
    outcome = await gateway.send_turn("do the thing")
    assert outcome.output_text == "ok"
    assert outcome.session_id == "conv-1"
    argv = scripted.invocations[0].argv
    assert argv[0] == "agy"
    assert "--sandbox" in argv
    assert "--conversation" in argv
    assert "-c" not in argv
    assert "--dangerously-skip-permissions" not in argv
    # Default (autonomous) mode should allow workspace commands
    assert scripted.invocations[0].settings["toolPermission"] in ("ask", "allow")
    assert "allow" in scripted.invocations[0].settings["permissions"]


@pytest.mark.asyncio
async def test_cli_gateway_uses_stderr_when_stdout_empty(tmp_path: Path) -> None:
    scripted = _ScriptedAgy(
        [
            subprocess.CompletedProcess(
                args=["agy"],
                returncode=0,
                stdout="",
                stderr="pong\nAGYLOOP_TASK_FULLY_COMPLETE\n",
            )
        ]
    )
    gateway = AgyCliAgentGateway(cwd=str(tmp_path), runner=scripted)
    outcome = await gateway.send_turn("go")
    assert "pong" in (outcome.output_text or "")


@pytest.mark.asyncio
async def test_cli_gateway_empty_print_is_config_error(tmp_path: Path) -> None:
    scripted = _ScriptedAgy(
        [subprocess.CompletedProcess(args=["agy"], returncode=0, stdout="", stderr="")]
    )
    gateway = AgyCliAgentGateway(cwd=str(tmp_path), runner=scripted)
    with pytest.raises(AgentConfigError, match="empty print"):
        await gateway.send_turn("go")


@pytest.mark.asyncio
async def test_cli_gateway_nonzero_non_capacity_is_config_error(tmp_path: Path) -> None:
    scripted = _ScriptedAgy(
        [
            subprocess.CompletedProcess(
                args=["agy"],
                returncode=1,
                stdout="",
                stderr="sandbox: command failed",
            )
        ]
    )
    gateway = AgyCliAgentGateway(cwd=str(tmp_path), runner=scripted)
    with pytest.raises(AgentConfigError, match="sandbox: command failed"):
        await gateway.send_turn("go")


@pytest.mark.asyncio
async def test_cli_gateway_maps_429_into_window_signals(tmp_path: Path) -> None:
    scripted = _ScriptedAgy(
        [
            subprocess.CompletedProcess(
                args=["agy"],
                returncode=1,
                stdout="",
                stderr="429 RESOURCE_EXHAUSTED RPM",
            )
        ]
    )
    gateway = AgyCliAgentGateway(cwd=str(tmp_path), runner=scripted)
    outcome = await gateway.send_turn("go")
    capacity = classify(outcome.signals)
    assert isinstance(capacity, WindowExhausted)
    assert capacity.rate_limit_type == "rpm"


@pytest.mark.asyncio
async def test_cli_gateway_unsafe_skip_emits_flag_after_gates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / ".git").mkdir()
    monkeypatch.setattr("agyloop.infrastructure.agent.cli_argv.os.geteuid", lambda: 501)
    scripted = _ScriptedAgy(
        [subprocess.CompletedProcess(args=["agy"], returncode=0, stdout="ok", stderr="")]
    )
    gateway = AgyCliAgentGateway(
        cwd=str(tmp_path),
        unsafe_skip_permissions=True,
        runner=scripted,
    )
    await gateway.send_turn("go")
    argv = scripted.invocations[0].argv
    assert "--dangerously-skip-permissions" in argv
    assert "--sandbox" not in argv


@pytest.mark.asyncio
async def test_cli_gateway_refuses_skip_outside_git(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("agyloop.infrastructure.agent.cli_argv.os.geteuid", lambda: 501)
    gateway = AgyCliAgentGateway(
        cwd=str(tmp_path),
        unsafe_skip_permissions=True,
        runner=_ScriptedAgy([]),
    )
    with pytest.raises(UnsafeSkipPermissionsError):
        await gateway.send_turn("go")


@pytest.mark.asyncio
async def test_cli_gateway_missing_agy_raises_when_using_real_runner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("agyloop.infrastructure.agent.gateway_cli.shutil.which", lambda _: None)
    gateway = AgyCliAgentGateway(cwd=str(tmp_path))
    with pytest.raises(AgentConfigError, match="agy CLI not found"):
        await gateway.send_turn("go")


@pytest.mark.asyncio
async def test_cli_gateway_helpers_and_execute_agy(tmp_path: Path) -> None:
    from unittest.mock import patch

    from agyloop.domain.model_profile import ModelEffortProfile
    from agyloop.infrastructure.agent.gateway_cli import execute_agy

    # execute_agy with settings
    inv = AgyCliInvocation(argv=["echo", "hi"], settings={"toolPermission": "sandbox"})
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=["echo"], returncode=0, stdout="hi\n"
        )
        res = execute_agy(inv, cwd=tmp_path)
        assert res.returncode == 0
        assert (tmp_path / ".agyloop" / "cli-settings.json").is_file()

    # Helper methods on AgyCliAgentGateway
    gateway = AgyCliAgentGateway(
        cwd=str(tmp_path),
        print_timeout="10m",
        runner=_ScriptedAgy(
            [subprocess.CompletedProcess(args=["agy"], returncode=0, stdout="done")]
        ),
    )
    assert gateway.resolve_tool_approval("r1", allow=True) is False
    await gateway.set_profile(ModelEffortProfile(model="gemini-2.5-flash", effort="low"))
    assert gateway._model == "gemini-2.5-flash"
    await gateway.set_permission_mode("scoped")
    await gateway.set_permission_mode("not-a-real-mode")  # unrecognized: no-op
    assert gateway._permission_mode == "scoped"
    await gateway.set_cwd(str(tmp_path / "new_cwd"))
    assert gateway._cwd == tmp_path / "new_cwd"
    await gateway.set_session_resources(foo="bar")
    outcome = await gateway.send_turn("hello")
    assert outcome.output_text == "done"
    await gateway.close()
