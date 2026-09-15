# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from agyloop.application.dto import RunResult
from agyloop.application.usecases.doctor import (
    AuthResolution,
    DoctorCheck,
    HarnessStatus,
    all_passed,
    run_doctor,
)
from agyloop.application.usecases.list_sessions import list_sessions
from agyloop.application.usecases.resume_session import resolve_last_run, resume_explicit
from agyloop.application.usecases.run_plan import (
    run_from_plan_file,
    with_done_marker_instruction,
)
from agyloop.domain.errors import InvalidSessionSelectorError
from agyloop.domain.session import SessionRef


def test_with_done_marker_instruction_appends_agyloop_marker() -> None:
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
    assert "AGYLOOP_TASK_FULLY_COMPLETE" in initial
    assert "Continue exactly where you left off." in continue_prompt


async def test_resume_explicit_sends_a_continue_style_prompt() -> None:
    expected = RunResult(
        success=True, reason="done", session_id="sid", turns_spent=1, dollars_spent=0.0
    )
    stub = _StubRunner(expected)
    result = await resume_explicit(stub)  # type: ignore[arg-type]
    assert result is expected
    initial, continue_prompt = stub.calls[0]
    assert initial == continue_prompt


class _FakeCatalog:
    def __init__(self, refs: list[SessionRef]) -> None:
        self._refs = refs

    def most_recent(self, cwd: str) -> SessionRef | None:
        del cwd
        return self._refs[-1] if self._refs else None

    def list_all(self, cwd: str | None = None) -> list[SessionRef]:
        del cwd
        return list(self._refs)


def test_resolve_last_run_returns_the_session_when_found() -> None:
    ref = SessionRef(session_id="abc", cwd="/repo")
    catalog = _FakeCatalog([ref])
    assert resolve_last_run(catalog, "/repo") is ref  # type: ignore[arg-type]


def test_resolve_last_run_raises_when_registry_empty() -> None:
    catalog = _FakeCatalog([])
    with pytest.raises(InvalidSessionSelectorError, match="cannot be enumerated"):
        resolve_last_run(catalog, "/repo")  # type: ignore[arg-type]


def test_list_sessions_delegates_to_the_catalog() -> None:
    ref = SessionRef(session_id="abc", cwd="/repo")
    catalog = _FakeCatalog([ref])
    assert list_sessions(catalog, "/repo") == [ref]  # type: ignore[arg-type]


class _FakeDoctorEnv:
    def __init__(
        self,
        *,
        auth: AuthResolution,
        interactive_hooks: bool = False,
        agy_path: str | None = None,
        agy_version: str | None = None,
        mcp_servers: list[str] | None = None,
        harness_status: HarnessStatus | None = None,
    ) -> None:
        self._auth = auth
        self._interactive_hooks = interactive_hooks
        self._agy_path = agy_path
        self._agy_version = agy_version
        self._mcp_servers = mcp_servers or []
        self._harness_status = harness_status or HarnessStatus(
            available=False, detail="test harness (not available)"
        )

    def resolve_auth(self) -> AuthResolution:
        return self._auth

    def interactive_hooks_registered(self) -> bool:
        return self._interactive_hooks

    def find_agy_cli(self) -> str | None:
        return self._agy_path

    def agy_cli_version(self, path: str) -> str | None:
        del path
        return self._agy_version

    def configured_mcp_servers(self) -> list[str]:
        return self._mcp_servers

    def check_sdk_harness(self) -> HarnessStatus:
        return self._harness_status


def _authed_developer() -> AuthResolution:
    return AuthResolution(
        lane="developer_api",
        source="GOOGLE_API_KEY",
        authenticated=True,
        detail="Developer API via GOOGLE_API_KEY",
    )


def test_run_doctor_reports_auth_lane_and_source(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    env = _FakeDoctorEnv(auth=_authed_developer())
    checks = run_doctor(env, cwd=tmp_path)
    auth_check = next(c for c in checks if c.name == "authentication")
    assert auth_check.passed is True
    assert "developer_api" in auth_check.detail
    assert "GOOGLE_API_KEY" in auth_check.detail
    assert all_passed(checks) is True


def test_run_doctor_fails_when_unauthenticated(tmp_path: Path) -> None:
    env = _FakeDoctorEnv(
        auth=AuthResolution(
            lane="unresolved",
            source="none",
            authenticated=False,
            detail="no GOOGLE_API_KEY and no ADC",
        )
    )
    checks = run_doctor(env, cwd=tmp_path)
    auth_check = next(c for c in checks if c.name == "authentication")
    assert auth_check.passed is False
    assert all_passed(checks) is False


def test_run_doctor_fails_when_interactive_hooks_registered(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    env = _FakeDoctorEnv(auth=_authed_developer(), interactive_hooks=True)
    checks = run_doctor(env, cwd=tmp_path)
    hook_check = next(c for c in checks if c.name == "interactive-hooks")
    assert hook_check.passed is False
    assert all_passed(checks) is False


def test_run_doctor_flags_mcp_servers(tmp_path: Path) -> None:
    env = _FakeDoctorEnv(auth=_authed_developer(), mcp_servers=["server-a"])
    checks = run_doctor(env, cwd=tmp_path)
    mcp_check = next(c for c in checks if c.name == "mcp-servers")
    assert mcp_check.passed is False
    assert "server-a" in mcp_check.detail


def test_doctor_check_is_a_plain_value_object() -> None:
    check = DoctorCheck(name="x", passed=True, detail="ok")
    assert check.name == "x"


def test_session_ref_used_by_list_has_timestamp() -> None:
    ref = SessionRef(
        session_id="abc",
        cwd="/repo",
        last_modified=datetime(2026, 8, 13, tzinfo=UTC),
    )
    assert ref.last_modified is not None
