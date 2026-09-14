# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from pathlib import Path

import pytest

from claudeloop.application.dto import RunResult
from claudeloop.application.usecases.doctor import DoctorCheck, all_passed, run_doctor
from claudeloop.application.usecases.list_sessions import list_sessions
from claudeloop.application.usecases.resume_session import resolve_most_recent, resume_explicit
from claudeloop.application.usecases.run_control import request_wind_down
from claudeloop.application.usecases.run_plan import (
    run_from_plan_file,
    with_done_marker_instruction,
)
from claudeloop.domain.control import WindDownCommand
from claudeloop.domain.errors import InvalidSessionSelectorError
from claudeloop.domain.session import SessionRef

# --- run_plan ---


def test_with_done_marker_instruction_appends_the_marker_text() -> None:
    result = with_done_marker_instruction("do the thing", "MY_MARKER")
    assert "do the thing" in result
    assert "MY_MARKER" in result


class _StubRunner:
    def __init__(self, result: RunResult) -> None:
        self._result = result
        self.calls: list[tuple[str, str]] = []

    async def run(self, *, initial_prompt: str, continue_prompt: str) -> RunResult:
        self.calls.append((initial_prompt, continue_prompt))
        return self._result


async def test_run_from_plan_file_reads_the_file_and_delegates_to_runner(tmp_path: Path) -> None:
    plan_path = tmp_path / "handoff.md"
    plan_path.write_text("- [ ] do the thing\n")
    expected = RunResult(
        success=True, reason="done", session_id="sid", turns_spent=1, dollars_spent=0.0
    )
    stub = _StubRunner(expected)

    result = await run_from_plan_file(stub, plan_path)  # type: ignore[arg-type]

    assert result is expected
    assert len(stub.calls) == 1
    initial, continue_prompt = stub.calls[0]
    assert "do the thing" in initial
    assert "CLAUDELOOP_TASK_FULLY_COMPLETE" in initial
    assert "Continue exactly where you left off." in continue_prompt


# --- resume_session ---


async def test_resume_explicit_sends_a_single_continue_style_prompt() -> None:
    expected = RunResult(
        success=True, reason="done", session_id="sid", turns_spent=1, dollars_spent=0.0
    )
    stub = _StubRunner(expected)
    result = await resume_explicit(stub)  # type: ignore[arg-type]
    assert result is expected
    initial, continue_prompt = stub.calls[0]
    assert initial == continue_prompt  # resume uses the same marker-wrapped prompt both times


class _FakeCatalog:
    def __init__(self, ref: SessionRef | None) -> None:
        self._ref = ref

    def most_recent(self, cwd: str) -> SessionRef | None:
        return self._ref

    def list_all(self, cwd: str | None = None) -> list[SessionRef]:
        return [self._ref] if self._ref else []


def test_resolve_most_recent_returns_the_session_when_found() -> None:
    ref = SessionRef(session_id="abc", cwd="/repo")
    catalog = _FakeCatalog(ref)
    assert resolve_most_recent(catalog, "/repo") is ref  # type: ignore[arg-type]


def test_resolve_most_recent_raises_a_clear_error_when_none_found() -> None:
    catalog = _FakeCatalog(None)
    with pytest.raises(InvalidSessionSelectorError, match="No prior Claude Code sessions"):
        resolve_most_recent(catalog, "/repo")  # type: ignore[arg-type]


# --- list_sessions ---


def test_list_sessions_delegates_to_the_catalog() -> None:
    ref = SessionRef(session_id="abc", cwd="/repo")
    catalog = _FakeCatalog(ref)
    assert list_sessions(catalog, "/repo") == [ref]  # type: ignore[arg-type]


# --- doctor ---


class _FakeDoctorEnv:
    def __init__(
        self,
        *,
        cli_path: str | None,
        version: str | None,
        authed: bool,
        mcp_servers: list[str],
        anthropic_version: str | None = "0.0.0",
        api_count: int | None = 137,
    ) -> None:
        self._cli_path = cli_path
        self._version = version
        self._authed = authed
        self._mcp_servers = mcp_servers
        self._anthropic_version = anthropic_version
        self._api_count = api_count

    def find_claude_cli(self) -> str | None:
        return self._cli_path

    def claude_cli_version(self, path: str) -> str | None:
        return self._version

    def is_authenticated(self) -> bool:
        return self._authed

    def configured_mcp_servers(self) -> list[str]:
        return self._mcp_servers

    def anthropic_sdk_version(self) -> str | None:
        return self._anthropic_version

    def api_surface_method_count(self) -> int | None:
        return self._api_count


def test_run_doctor_all_green(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    env = _FakeDoctorEnv(cli_path="/usr/bin/claude", version="1.0", authed=True, mcp_servers=[])
    checks = run_doctor(env, cwd=tmp_path)  # type: ignore[arg-type]
    assert all_passed(checks) is True
    assert {c.name for c in checks} == {
        "claude-cli",
        "authentication",
        "mcp-servers",
        "anthropic-sdk",
        "api-surface",
        "working-directory",
    }


def test_run_doctor_missing_cli() -> None:
    env = _FakeDoctorEnv(cli_path=None, version=None, authed=False, mcp_servers=[])
    checks = run_doctor(env, cwd=Path("/tmp"))  # type: ignore[arg-type]
    cli_check = next(c for c in checks if c.name == "claude-cli")
    assert cli_check.passed is False
    assert "not found" in cli_check.detail


def test_run_doctor_flags_mcp_servers_as_needing_manual_verification(tmp_path: Path) -> None:
    env = _FakeDoctorEnv(
        cli_path="/usr/bin/claude",
        version="1.0",
        authed=True,
        mcp_servers=["server-a", "server-b"],
    )
    checks = run_doctor(env, cwd=tmp_path)  # type: ignore[arg-type]
    mcp_check = next(c for c in checks if c.name == "mcp-servers")
    assert mcp_check.passed is False
    assert "server-a" in mcp_check.detail
    assert all_passed(checks) is False


def test_run_doctor_flags_non_git_working_directory(tmp_path: Path) -> None:
    env = _FakeDoctorEnv(cli_path="/usr/bin/claude", version="1.0", authed=True, mcp_servers=[])
    checks = run_doctor(env, cwd=tmp_path)  # type: ignore[arg-type]
    wd_check = next(c for c in checks if c.name == "working-directory")
    assert wd_check.passed is False


def test_run_doctor_reports_missing_api_surface_verification(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    env = _FakeDoctorEnv(
        cli_path="/usr/bin/claude",
        version="1.0",
        authed=True,
        mcp_servers=[],
        api_count=None,
    )
    checks = run_doctor(env, cwd=tmp_path)  # type: ignore[arg-type]
    api_check = next(c for c in checks if c.name == "api-surface")
    assert api_check.passed is False
    assert "baseline" in api_check.detail


def test_doctor_check_is_a_plain_value_object() -> None:
    check = DoctorCheck(name="x", passed=True, detail="ok")
    assert check.name == "x"
    assert check.passed is True


def test_all_passed_empty_list_is_true() -> None:
    assert all_passed([]) is True


class _FakeInbox:
    def __init__(self) -> None:
        self.commands: list[object] = []

    def enqueue(self, command: object) -> object:
        self.commands.append(command)
        return command


def test_request_wind_down_enqueues_the_command_with_its_reason() -> None:
    inbox = _FakeInbox()
    result = request_wind_down(inbox, reason="rotate", run_id="run-1")
    assert result.run_id == "run-1"
    assert result.command_type == "wind_down"
    assert inbox.commands == [WindDownCommand(reason="rotate")]
