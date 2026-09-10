# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

import re
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner, Result

from agyloop import __version__
from agyloop.application.dto import RunResult
from agyloop.application.usecases.doctor import AuthResolution, HarnessStatus
from agyloop.bootstrap import RunnerContext, build_runner
from agyloop.cli import asyncio as cli_asyncio
from agyloop.cli.app import app
from agyloop.domain.session import SessionRef
from agyloop.infrastructure.agent.cli_argv import UNSAFE_SKIP_WARNING
from agyloop.infrastructure.rundir import (
    RunDirectory,
    list_run_directories,
    runs_root_for,
)

runner = CliRunner()

_NO_COLOR_ENV = {"NO_COLOR": "1", "TERM": "dumb", "FORCE_COLOR": "0", "COLUMNS": "120"}
_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")


def _invoke(*args: str, env: dict[str, str] | None = None) -> Result:
    merged = dict(_NO_COLOR_ENV)
    if env:
        merged.update(env)
    return runner.invoke(app, list(args), env=merged)


def _plain(text: str) -> str:
    return _ANSI_ESCAPE.sub("", text)


def test_version_option_reports_installed_version() -> None:
    result = _invoke("--version")

    assert result.exit_code == 0
    assert result.stdout.strip() == f"agyloop {__version__}"


def test_help_option_succeeds() -> None:
    result = _invoke("--help")

    assert result.exit_code == 0
    stdout = _plain(result.stdout)
    assert "Autonomous Google Antigravity" in stdout
    assert "run" in stdout
    assert "resume" in stdout
    assert "sessions" in stdout
    assert "doctor" in stdout


def _listed_commands(help_text: str) -> set[str]:
    """Command names from the Typer Commands section, not incidental help words."""
    names: set[str] = set()
    in_commands = False
    for line in help_text.splitlines():
        stripped = line.strip().lstrip("│").strip()
        if "commands" in stripped.lower() and stripped.lower().startswith(("commands", "╭")):
            in_commands = True
            continue
        if in_commands:
            if not stripped or stripped.startswith("╰"):
                break
            names.add(stripped.split()[0])
    return names


def test_api_command_is_generated() -> None:
    """Operator override 2026-08-13: ``agyloop api`` ships with a drift gate (ADR 0015)."""
    help_result = _invoke("--help")
    assert help_result.exit_code == 0
    help_text = _plain(help_result.stdout)
    commands = _listed_commands(help_text)
    assert "api" in commands
    assert "savepoints" in commands
    assert "snapshot" in commands
    assert "unwind" in commands
    assert "adr 0015" in help_text.lower()

    api_result = _invoke("api", "--help")
    assert api_result.exit_code == 0
    api_help = _plain(api_result.stdout)
    assert "models" in api_help.lower()
    assert "--lane" in api_help


def test_adr_0006_restates_stability_criterion() -> None:
    path = (
        Path(__file__).parents[1]
        / "docs"
        / "architecture"
        / "decisions"
        / "0006-defer-genai-rest.md"
    )
    text = path.read_text(encoding="utf-8").lower()
    assert "discovery document" in text
    assert "preview" in text
    assert "agyloop api" in text
    assert "two consecutive" in text
    assert "superseded" in text


def test_adr_0015_ships_rest_with_drift_gate() -> None:
    path = (
        Path(__file__).parents[1]
        / "docs"
        / "architecture"
        / "decisions"
        / "0015-generated-gemini-rest-with-drift-gate.md"
    )
    text = path.read_text(encoding="utf-8").lower()
    assert "drift" in text
    assert "agyloop api" in text
    assert "operator" in text
    assert "0006" in text


def test_run_help_renders() -> None:
    result = _invoke("run", "--help")

    assert result.exit_code == 0
    stdout = _plain(result.stdout)
    assert "PLAN" in stdout.upper() or "plan" in stdout
    assert "--no-probe" in stdout
    assert "--model" in stdout
    assert "--max-turns" in stdout
    assert "--max-wait" in stdout
    assert "--unsafe-skip" in stdout
    assert "--ramp" in stdout
    assert "--gateway" in stdout


def test_resume_help_renders() -> None:
    result = _invoke("resume", "--help")

    assert result.exit_code == 0
    stdout = _plain(result.stdout)
    assert "--conversation" in stdout
    assert "--last" in stdout
    assert "--ramp" in stdout
    assert "--gateway" in stdout


def test_sessions_help_states_registry_only_limitation() -> None:
    result = _invoke("sessions", "--help")

    assert result.exit_code == 0
    stdout = _plain(result.stdout).lower()
    assert "cannot enumerate" in stdout or "cannot list vendor" in stdout
    assert "vendor" in stdout or "conversation" in stdout


def test_doctor_help_renders() -> None:
    result = _invoke("doctor", "--help")

    assert result.exit_code == 0
    stdout = _plain(result.stdout).lower()
    assert "auth" in stdout or "google_api_key" in stdout or "pre-flight" in stdout


def test_cli_package_does_not_import_infrastructure() -> None:
    root = Path(__file__).parents[1] / "src" / "agyloop" / "cli"
    source = "\n".join(path.read_text() for path in root.rglob("*.py"))
    assert "agyloop.infrastructure" not in source


def test_async_bridge_is_asyncio_run() -> None:
    assert hasattr(cli_asyncio, "async_command")
    source = (Path(__file__).parents[1] / "src" / "agyloop" / "cli" / "asyncio.py").read_text()
    calls = [
        line
        for line in source.splitlines()
        if "asyncio.run(" in line and not line.strip().startswith("#")
    ]
    assert len(calls) == 1


def test_doctor_cli_reports_resolved_lane(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    class _FakeEnv:
        def resolve_auth(self) -> AuthResolution:
            return AuthResolution(
                lane="developer_api",
                source="GOOGLE_API_KEY",
                authenticated=True,
                detail="Developer API via GOOGLE_API_KEY",
            )

        def interactive_hooks_registered(self) -> bool:
            return False

        def find_agy_cli(self) -> str | None:
            return None

        def agy_cli_version(self, path: str) -> str | None:
            del path
            return None

        def configured_mcp_servers(self) -> list[str]:
            return []

        def check_sdk_harness(self) -> HarnessStatus:
            return HarnessStatus(available=True, detail="stock harness available")

    monkeypatch.setattr("agyloop.bootstrap.build_doctor_environment", lambda: _FakeEnv())
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".git").mkdir()
    result = _invoke("doctor")
    assert result.exit_code == 0
    stdout = _plain(result.stdout)
    assert "developer_api" in stdout
    assert "GOOGLE_API_KEY" in stdout
    assert "AI Studio" in stdout


def test_sessions_cli_lists_registry_only(tmp_path: Path) -> None:
    directory = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    directory.update_meta(conversation_id="conv-listed")
    result = _invoke("sessions", "--cwd", str(tmp_path))
    assert result.exit_code == 0
    stdout = _plain(result.stdout)
    assert "conv-listed" in stdout
    assert "cannot be enumerated" in stdout.lower() or "not vendor" in stdout.lower()


def test_run_cli_uses_bootstrap_runner(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text("- [ ] do the thing\n", encoding="utf-8")
    seen: dict[str, object] = {}

    class _StubRunner:
        async def run(self, *, initial_prompt: str, continue_prompt: str) -> RunResult:
            seen["initial"] = initial_prompt
            del continue_prompt
            return RunResult(
                success=True,
                reason="done",
                session_id="sid",
                turns_spent=1,
                dollars_spent=0.0,
            )

    class _Ctx:
        runner = _StubRunner()
        run_id = "run-test"

    def _build_runner(**kwargs: object) -> _Ctx:
        seen["kwargs"] = kwargs
        return _Ctx()

    monkeypatch.setattr("agyloop.bootstrap.build_runner", _build_runner)
    result = _invoke("run", str(plan), "--cwd", str(tmp_path), "--no-probe")
    assert result.exception is None, result.exception
    assert result.exit_code == 0
    assert "do the thing" in str(seen["initial"])
    kwargs = seen["kwargs"]
    assert isinstance(kwargs, dict)
    assert kwargs["no_probe"] is True


def test_run_cli_passes_strict_autonomy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text("- [ ] do the thing\n", encoding="utf-8")
    seen: dict[str, object] = {}

    class _StubRunner:
        async def run(self, *, initial_prompt: str, continue_prompt: str) -> RunResult:
            del initial_prompt, continue_prompt
            return RunResult(
                success=True,
                reason="done",
                session_id="sid",
                turns_spent=1,
                dollars_spent=0.0,
            )

    class _Ctx:
        runner = _StubRunner()
        run_id = "run-test"

    def _build_runner(**kwargs: object) -> _Ctx:
        seen["kwargs"] = kwargs
        return _Ctx()

    monkeypatch.setattr("agyloop.bootstrap.build_runner", _build_runner)
    result = _invoke("run", str(plan), "--cwd", str(tmp_path), "--strict-autonomy")
    assert result.exception is None, result.exception
    assert result.exit_code == 0
    kwargs = seen["kwargs"]
    assert isinstance(kwargs, dict)
    assert kwargs["strict_autonomy"] is True


def test_resume_last_seeds_from_plan_md_not_truncated_preview(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first = "Keep this heading " + ("x" * 250)
    plan = tmp_path / "source-plan.md"
    plan.write_text(f"{first}\n- [ ] second line must survive degrade seed\n", encoding="utf-8")
    directory = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path, plan_path=plan)
    directory.update_meta(conversation_id="conv-seed")
    original_run_id = directory.read_meta().run_id
    captured: dict[str, object] = {}

    class _StubRunner:
        async def run(self, *, initial_prompt: str, continue_prompt: str) -> RunResult:
            del initial_prompt, continue_prompt
            return RunResult(
                success=True,
                reason="done",
                session_id="sid",
                turns_spent=1,
                dollars_spent=0.0,
            )

    def _build_runner(**kwargs: object) -> RunnerContext:
        ctx = build_runner(**kwargs)  # type: ignore[arg-type]
        captured["cli_plan_seed"] = kwargs.get("plan_seed")
        captured["gateway_seed"] = ctx.gateway._plan_seed  # type: ignore[attr-defined]
        captured["run_id"] = ctx.run_id
        return RunnerContext(
            runner=_StubRunner(),  # type: ignore[arg-type]
            gateway=ctx.gateway,
            run_dir=ctx.run_dir,
            run_id=ctx.run_id,
            trace_id=ctx.trace_id,
        )

    monkeypatch.setattr("agyloop.bootstrap.build_runner", _build_runner)
    result = _invoke("resume", "--last", "--cwd", str(tmp_path), "--no-probe")
    assert result.exception is None, result.exception
    assert result.exit_code == 0
    cli_seed = captured["cli_plan_seed"]
    assert cli_seed != first[:200]
    gateway_seed = captured["gateway_seed"]
    assert isinstance(gateway_seed, str)
    assert "- [ ] second line must survive degrade seed" in gateway_seed
    assert captured["run_id"] == original_run_id
    assert len(list_run_directories(tmp_path)) == 1


def test_resume_last_survives_preflight_persist_of_null_session_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    directory = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    directory.update_meta(conversation_id="conv-keep")
    directory.update_meta(session_id=None, phase="WAITING", status="waiting")
    assert directory.read_meta().conversation_id == "conv-keep"
    captured: dict[str, object] = {}

    class _StubRunner:
        async def run(self, *, initial_prompt: str, continue_prompt: str) -> RunResult:
            del initial_prompt, continue_prompt
            return RunResult(
                success=True,
                reason="done",
                session_id="sid",
                turns_spent=1,
                dollars_spent=0.0,
            )

    def _build_runner(**kwargs: object) -> RunnerContext:
        ctx = build_runner(**kwargs)  # type: ignore[arg-type]
        captured["conversation_id"] = kwargs.get("conversation_id")
        captured["run_id"] = ctx.run_id
        return RunnerContext(
            runner=_StubRunner(),  # type: ignore[arg-type]
            gateway=ctx.gateway,
            run_dir=ctx.run_dir,
            run_id=ctx.run_id,
            trace_id=ctx.trace_id,
        )

    monkeypatch.setattr("agyloop.bootstrap.build_runner", _build_runner)
    result = _invoke("resume", "--last", "--cwd", str(tmp_path), "--no-probe")
    assert result.exception is None, result.exception
    assert result.exit_code == 0
    assert captured["conversation_id"] == "conv-keep"
    assert captured["run_id"] == directory.read_meta().run_id


def test_resume_without_registry_fails_cleanly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class _EmptyCatalog:
        def most_recent(self, cwd: str) -> SessionRef | None:
            del cwd
            return None

        def list_all(self, cwd: str | None = None) -> list[SessionRef]:
            del cwd
            return []

    monkeypatch.setattr("agyloop.bootstrap.build_session_catalog", lambda: _EmptyCatalog())
    result = _invoke("resume", "--last", "--cwd", str(tmp_path))
    assert result.exit_code == 1
    assert (
        "cannot be enumerated" in _plain(result.output).lower()
        or "no prior" in _plain(result.output).lower()
    )


def test_stop_enqueues_for_latest_run(tmp_path: Path) -> None:
    directory = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    result = _invoke("stop", "--cwd", str(tmp_path))
    assert result.exit_code == 0
    run_id = directory.read_meta().run_id
    assert run_id in _plain(result.stdout)
    inbox_files = list(directory.inbox.glob("*.cmd.json"))
    assert len(inbox_files) == 1
    assert "stop" in inbox_files[0].read_text(encoding="utf-8")


def test_prompt_now_enqueues_for_latest_run(tmp_path: Path) -> None:
    directory = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    result = _invoke("prompt", "keep going", "--now", "--cwd", str(tmp_path))
    assert result.exit_code == 0
    stdout = _plain(result.stdout)
    assert "prompt_now" in stdout
    assert directory.read_meta().run_id in stdout
    inbox_files = list(directory.inbox.glob("*.cmd.json"))
    assert len(inbox_files) == 1
    assert "prompt_now" in inbox_files[0].read_text(encoding="utf-8")


def test_prompt_requires_now_or_at_break() -> None:
    result = _invoke("prompt", "hello")
    assert result.exit_code == 2
    assert "exactly one" in _plain(result.output).lower()


def test_stop_without_runs_fails_cleanly(tmp_path: Path) -> None:
    result = _invoke("stop", "--cwd", str(tmp_path))
    assert result.exit_code == 1
    assert "no agyloop runs" in _plain(result.output).lower()


@pytest.mark.parametrize(
    ("args", "success_text"),
    [
        (("stop",), "stop requested"),
        (("prompt", "keep going", "--now"), "enqueued"),
    ],
)
def test_control_command_refuses_completed_run(
    tmp_path: Path,
    args: tuple[str, ...],
    success_text: str,
) -> None:
    directory = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    directory.update_meta(status="finished")

    result = _invoke(*args, "--cwd", str(tmp_path))

    output = _plain(result.output).lower()
    assert result.exit_code == 1
    assert "active" in output
    assert success_text not in output
    assert list(directory.inbox.glob("*.cmd.json")) == []


def test_stop_prefers_newest_active_run(tmp_path: Path) -> None:
    active = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    completed = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    completed.update_meta(status="finished")

    result = _invoke("stop", "--cwd", str(tmp_path))

    assert result.exit_code == 0
    assert active.read_meta().run_id in _plain(result.stdout)
    assert len(list(active.inbox.glob("*.cmd.json"))) == 1
    assert list(completed.inbox.glob("*.cmd.json")) == []


def test_run_unsafe_skip_permissions_refuses_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / ".git").mkdir()
    plan = tmp_path / "plan.md"
    plan.write_text("- [ ] do the thing\n", encoding="utf-8")

    def _must_not_build(**kwargs: object) -> None:
        del kwargs
        raise AssertionError("build_runner must not run after a root refuse")

    monkeypatch.setattr("agyloop.bootstrap.build_runner", _must_not_build)
    with patch("agyloop.infrastructure.agent.cli_argv.os.geteuid", return_value=0):
        result = _invoke(
            "run",
            str(plan),
            "--cwd",
            str(tmp_path),
            "--unsafe-skip-permissions",
        )
    combined = _plain(result.stdout + result.stderr + result.output).lower()
    assert result.exit_code != 0
    assert "root" in combined
    assert UNSAFE_SKIP_WARNING.lower() in combined


def test_run_unsafe_skip_permissions_refuses_outside_git(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text("- [ ] do the thing\n", encoding="utf-8")

    def _must_not_build(**kwargs: object) -> None:
        del kwargs
        raise AssertionError("build_runner must not run outside git")

    monkeypatch.setattr("agyloop.bootstrap.build_runner", _must_not_build)
    with patch("agyloop.infrastructure.agent.cli_argv.os.geteuid", return_value=501):
        result = _invoke(
            "run",
            str(plan),
            "--cwd",
            str(tmp_path),
            "--unsafe-skip-permissions",
        )
    combined = _plain(result.stdout + result.stderr + result.output).lower()
    assert result.exit_code != 0
    assert "git repository" in combined
    assert UNSAFE_SKIP_WARNING.lower() in combined


def test_run_unsafe_skip_permissions_refuses_sdk_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / ".git").mkdir()
    plan = tmp_path / "plan.md"
    plan.write_text("- [ ] do the thing\n", encoding="utf-8")

    def _must_not_build(**kwargs: object) -> None:
        del kwargs
        raise AssertionError("build_runner must not run for SDK unsafe-skip")

    monkeypatch.setattr("agyloop.bootstrap.build_runner", _must_not_build)
    with patch("agyloop.infrastructure.agent.cli_argv.os.geteuid", return_value=501):
        result = _invoke(
            "run",
            str(plan),
            "--cwd",
            str(tmp_path),
            "--unsafe-skip-permissions",
        )
    combined = _plain(result.stdout + result.stderr + result.output)
    lowered = combined.lower()
    assert result.exit_code != 0
    assert "36" in combined
    assert UNSAFE_SKIP_WARNING in combined
    assert "build_agy_argv" in combined
    assert "sdk" in lowered
    assert "yolo" in lowered
    assert "dangerously-skip-permissions" in lowered
    assert result.exception is None or not isinstance(result.exception, AssertionError)


def test_run_cli_passes_ramp_and_gateway(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text("- [ ] do the thing\n", encoding="utf-8")
    seen: dict[str, object] = {}

    class _StubRunner:
        async def run(self, *, initial_prompt: str, continue_prompt: str) -> RunResult:
            del initial_prompt, continue_prompt
            return RunResult(
                success=True,
                reason="done",
                session_id="sid",
                turns_spent=1,
                dollars_spent=0.0,
            )

    class _Ctx:
        runner = _StubRunner()
        run_id = "run-test"

    def _build_runner(**kwargs: object) -> _Ctx:
        seen["kwargs"] = kwargs
        return _Ctx()

    monkeypatch.setattr("agyloop.bootstrap.build_runner", _build_runner)
    result = _invoke(
        "run",
        str(plan),
        "--cwd",
        str(tmp_path),
        "--ramp",
        "5",
        "--gateway",
        "cli",
    )
    assert result.exception is None, result.exception
    assert result.exit_code == 0
    kwargs = seen["kwargs"]
    assert isinstance(kwargs, dict)
    assert kwargs["ramp"] == 5
    assert kwargs["gateway"] == "cli"


def test_run_gateway_cli_unsafe_skip_reaches_build_runner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / ".git").mkdir()
    plan = tmp_path / "plan.md"
    plan.write_text("- [ ] do the thing\n", encoding="utf-8")
    seen: dict[str, object] = {}

    class _StubRunner:
        async def run(self, *, initial_prompt: str, continue_prompt: str) -> RunResult:
            del initial_prompt, continue_prompt
            return RunResult(
                success=True,
                reason="done",
                session_id="sid",
                turns_spent=1,
                dollars_spent=0.0,
            )

    class _Ctx:
        runner = _StubRunner()
        run_id = "run-test"

    def _build_runner(**kwargs: object) -> _Ctx:
        seen["kwargs"] = kwargs
        return _Ctx()

    monkeypatch.setattr("agyloop.bootstrap.build_runner", _build_runner)
    with patch("agyloop.infrastructure.agent.cli_argv.os.geteuid", return_value=501):
        result = _invoke(
            "run",
            str(plan),
            "--cwd",
            str(tmp_path),
            "--gateway",
            "cli",
            "--unsafe-skip-permissions",
        )
    assert result.exception is None, result.exception
    assert result.exit_code == 0
    kwargs = seen["kwargs"]
    assert isinstance(kwargs, dict)
    assert kwargs["gateway"] == "cli"
    assert kwargs["unsafe_skip_permissions"] is True


def test_snapshot_cli_writes_files(tmp_path: Path) -> None:
    directory = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    directory.update_meta(status="finished")
    result = _invoke("snapshot", "--cwd", str(tmp_path), "--run-id", directory.read_meta().run_id)
    assert result.exit_code == 0, result.output
    stdout = _plain(result.stdout)
    assert "snapshot_path:" in stdout
    assert (directory.snapshots_root / "latest.json").is_file()


def test_unwind_refuses_active_run(tmp_path: Path) -> None:
    directory = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    result = _invoke(
        "unwind",
        "--to",
        "1",
        "--cwd",
        str(tmp_path),
        "--run-id",
        directory.read_meta().run_id,
    )
    assert result.exit_code == 1
    assert "still active" in _plain(result.output).lower()


def test_savepoints_empty_for_run_without_index(tmp_path: Path) -> None:
    directory = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    directory.update_meta(status="finished")
    result = _invoke(
        "savepoints",
        "--cwd",
        str(tmp_path),
        "--run-id",
        directory.read_meta().run_id,
    )
    assert result.exit_code == 0
    assert "no save points" in _plain(result.stdout).lower()
