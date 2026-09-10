# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Doctor environment unit tests with injectable subprocess fakes."""

from __future__ import annotations

import subprocess
from pathlib import Path

from codexloop.infrastructure.doctor_env import CodexDoctorEnvironment


class _Proc:
    def __init__(self, code: int = 0, stdout: str = "", stderr: str = "") -> None:
        self.returncode = code
        self.stdout = stdout
        self.stderr = stderr


def test_doctor_reports_auth_mode_and_probe_strategies(tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def which(name: str) -> str | None:
        return "/bin/codex" if name == "codex" else None

    def run(argv: list[str], *, timeout: float = 10) -> _Proc:
        del timeout
        calls.append(list(argv))
        if argv[1:] == ["--version"]:
            return _Proc(0, "codex-cli 0.50.0")
        if argv[1:] == ["login", "status"]:
            return _Proc(0, "logged in")
        if argv[1:] == ["exec", "--help"]:
            return _Proc(0, "Usage: --json --ephemeral -c key=value")
        return _Proc(1, "")

    env = CodexDoctorEnvironment(
        environ={"OPENAI_API_KEY": "sk-test"},
        which=which,
        run=run,  # type: ignore[arg-type]
        home=tmp_path,
        minimum_version=(0, 40, 0),
        app_server_live=lambda: False,
        rollout_live=lambda: True,
        mcp_servers=lambda: ("needs-oauth",),
    )
    (tmp_path / ".git").mkdir()
    report = env.diagnose(cwd=tmp_path)

    assert report.auth_mode == "api_key"
    assert report.probe_strategies == {
        "exec": True,
        "app-server": False,
        "rollout": True,
    }
    by_name = {c.name: c for c in report.checks}
    assert by_name["codex-cli"].passed is True
    assert by_name["login-status"].passed is True
    assert by_name["exec-flags"].passed is True
    assert by_name["mcp-oauth"].passed is False
    assert "needs-oauth" in by_name["mcp-oauth"].detail
    assert report.all_passed is False
    assert any(c[:2] == ["/bin/codex", "--version"] for c in calls)


def test_doctor_fails_when_codex_missing(tmp_path: Path) -> None:
    env = CodexDoctorEnvironment(
        environ={},
        which=lambda _name: None,
        run=lambda *_a, **_k: (_ for _ in ()).throw(subprocess.TimeoutExpired("x", 1)),
        home=tmp_path,
        mcp_servers=lambda: (),
    )
    report = env.diagnose(cwd=tmp_path)
    assert report.auth_mode == "none"
    assert any(c.name == "codex-cli" and not c.passed for c in report.checks)


def test_doctor_probes_app_server_help_when_live_hook_omitted(tmp_path: Path) -> None:
    def which(name: str) -> str | None:
        return "/bin/codex" if name == "codex" else None

    def run(argv: list[str], *, timeout: float = 10) -> _Proc:
        del timeout
        if argv[1:] == ["--version"]:
            return _Proc(0, "codex-cli 0.50.0")
        if argv[1:] == ["login", "status"]:
            return _Proc(0, "logged in")
        if argv[1:] == ["exec", "--help"]:
            return _Proc(0, "Usage: --json --ephemeral -c key=value")
        if argv[1:] == ["app-server", "--help"]:
            return _Proc(0, "Usage: codex app-server --stdio")
        return _Proc(1, "")

    env = CodexDoctorEnvironment(
        environ={"OPENAI_API_KEY": "sk-test"},
        which=which,
        run=run,  # type: ignore[arg-type]
        home=tmp_path,
        rollout_live=lambda: False,
        mcp_servers=lambda: (),
    )
    (tmp_path / ".git").mkdir()
    report = env.diagnose(cwd=tmp_path)
    assert report.probe_strategies["app-server"] is True


def test_doctor_app_server_probe_handles_failures(tmp_path: Path) -> None:
    def which(name: str) -> str | None:
        return "/bin/codex" if name == "codex" else None

    def run_fail(argv: list[str], *, timeout: float = 10) -> _Proc:
        del timeout
        if argv[1:] == ["app-server", "--help"]:
            return _Proc(1, "")
        if argv[1:] == ["--version"]:
            return _Proc(0, "codex-cli 0.50.0")
        if argv[1:] == ["login", "status"]:
            return _Proc(0, "logged in")
        if argv[1:] == ["exec", "--help"]:
            return _Proc(0, "Usage: --json --ephemeral -c key=value")
        return _Proc(1, "")

    env = CodexDoctorEnvironment(
        environ={"OPENAI_API_KEY": "sk-test"},
        which=which,
        run=run_fail,  # type: ignore[arg-type]
        home=tmp_path,
        rollout_live=lambda: False,
        mcp_servers=lambda: (),
    )
    (tmp_path / ".git").mkdir()
    assert env.diagnose(cwd=tmp_path).probe_strategies["app-server"] is False

    def run_timeout(argv: list[str], *, timeout: float = 10) -> _Proc:
        del timeout
        if argv[1:] == ["app-server", "--help"]:
            raise subprocess.TimeoutExpired(argv, 1)
        if argv[1:] == ["--version"]:
            return _Proc(0, "codex-cli 0.50.0")
        if argv[1:] == ["login", "status"]:
            return _Proc(0, "logged in")
        if argv[1:] == ["exec", "--help"]:
            return _Proc(0, "Usage: --json --ephemeral -c key=value")
        return _Proc(1, "")

    env_timeout = CodexDoctorEnvironment(
        environ={"OPENAI_API_KEY": "sk-test"},
        which=which,
        run=run_timeout,  # type: ignore[arg-type]
        home=tmp_path,
        rollout_live=lambda: False,
        mcp_servers=lambda: (),
    )
    assert env_timeout.diagnose(cwd=tmp_path).probe_strategies["app-server"] is False


def _quiet_env(tmp_path: Path, environ: dict[str, str]) -> CodexDoctorEnvironment:
    return CodexDoctorEnvironment(
        environ=environ,
        which=lambda name: None,
        run=lambda argv, timeout=10: _Proc(1, ""),  # type: ignore[arg-type,misc]
        home=tmp_path,
        minimum_version=(0, 40, 0),
    )


def test_auth_mode_reads_the_chatgpt_plan_credential_file(tmp_path: Path) -> None:
    """Covered on a developer machine by accident -- ~/.codex/auth.json exists
    there and not on a fresh runner. `home` is injected so the branch is
    exercised deterministically instead."""
    codex_home = tmp_path / ".codex"
    codex_home.mkdir()
    (codex_home / "auth.json").write_text("{}", encoding="utf-8")

    assert _quiet_env(tmp_path, {})._auth_mode() == "chatgpt_plan"


def test_auth_mode_is_none_when_there_is_neither_key_nor_credential_file(
    tmp_path: Path,
) -> None:
    assert _quiet_env(tmp_path, {})._auth_mode() == "none"


def test_an_api_key_outranks_the_credential_file(tmp_path: Path) -> None:
    codex_home = tmp_path / ".codex"
    codex_home.mkdir()
    (codex_home / "auth.json").write_text("{}", encoding="utf-8")

    assert _quiet_env(tmp_path, {"OPENAI_API_KEY": "sk-test"})._auth_mode() == "api_key"
    assert _quiet_env(tmp_path, {"CODEX_API_KEY": "sk-test"})._auth_mode() == "api_key"
