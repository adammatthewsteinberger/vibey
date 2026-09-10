# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Doctor environment adapter — probes ``codex`` CLI, auth, and capacity sources."""

from __future__ import annotations

import os
import re
import shutil
import subprocess  # nosec B404 — fixed argv to ``codex`` only, never shell=True
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

from codexloop.application.usecases.doctor import DoctorCheck, DoctorReport

MINIMUM_CODEX_VERSION: tuple[int, int, int] = (0, 40, 0)
_REQUIRED_EXEC_FLAGS = ("--json", "--ephemeral", "-c")
_VERSION_RE = re.compile(r"(\d+)\.(\d+)\.(\d+)")


class CodexDoctorEnvironment:
    """Injectable doctor probes over ``codex`` and the local filesystem."""

    def __init__(
        self,
        *,
        environ: Mapping[str, str] | None = None,
        which: Callable[[str], str | None] | None = None,
        run: Callable[..., subprocess.CompletedProcess[str]] | None = None,
        home: Path | None = None,
        minimum_version: tuple[int, int, int] = MINIMUM_CODEX_VERSION,
        app_server_live: Callable[[], bool] | None = None,
        rollout_live: Callable[[], bool] | None = None,
        mcp_servers: Callable[[], Sequence[str]] | None = None,
    ) -> None:
        self._environ = dict(environ) if environ is not None else dict(os.environ)
        self._which = which if which is not None else shutil.which
        self._run = run if run is not None else _default_run
        self._home = home if home is not None else Path.home()
        self._minimum = minimum_version
        self._app_server_live = app_server_live
        self._rollout_live = rollout_live
        self._mcp_servers = mcp_servers

    def diagnose(self, *, cwd: Path) -> DoctorReport:
        checks: list[DoctorCheck] = []
        codex = self._which("codex")
        if codex is None:
            checks.append(
                DoctorCheck(
                    name="codex-cli",
                    passed=False,
                    detail="`codex` not found on PATH",
                )
            )
            version_ok = False
            version_text = None
        else:
            version_text = self._codex_version(codex)
            version_ok = self._version_meets_floor(version_text)
            checks.append(
                DoctorCheck(
                    name="codex-cli",
                    passed=version_ok,
                    detail=(
                        f"found at {codex} ({version_text or 'version unknown'}); "
                        f"minimum {'.'.join(str(p) for p in self._minimum)}"
                    ),
                )
            )

        login_ok = False
        if codex is not None:
            login_ok = self._login_status_ok(codex)
        checks.append(
            DoctorCheck(
                name="login-status",
                passed=login_ok,
                detail="codex login status exit 0" if login_ok else "codex login status failed",
            )
        )

        flags_ok = False
        if codex is not None:
            flags_ok = self._exec_help_has_flags(codex)
        checks.append(
            DoctorCheck(
                name="exec-flags",
                passed=flags_ok,
                detail=(
                    f"required flags present: {', '.join(_REQUIRED_EXEC_FLAGS)}"
                    if flags_ok
                    else f"missing one of {_REQUIRED_EXEC_FLAGS}"
                ),
            )
        )

        auth_mode = self._auth_mode()
        checks.append(
            DoctorCheck(
                name="auth-mode",
                passed=auth_mode != "none",
                detail=f"active auth mode: {auth_mode}",
            )
        )

        strategies = {
            "exec": True,
            "app-server": (
                self._app_server_live()
                if self._app_server_live is not None
                else self._probe_app_server_live()
            ),
            "rollout": self._rollout_live() if self._rollout_live else False,
        }
        checks.append(
            DoctorCheck(
                name="probe-strategies",
                passed=True,
                detail=(
                    "live: "
                    + ", ".join(name for name, live in strategies.items() if live)
                    + (
                        "; unavailable: "
                        + ", ".join(name for name, live in strategies.items() if not live)
                        if any(not live for live in strategies.values())
                        else ""
                    )
                ).rstrip("; "),
            )
        )

        mcp = list(self._mcp_servers()) if self._mcp_servers is not None else []
        if mcp:
            checks.append(
                DoctorCheck(
                    name="mcp-oauth",
                    passed=False,
                    detail=(
                        f"MCP servers requiring OAuth: {', '.join(mcp)} — "
                        "authorize before an unattended run"
                    ),
                )
            )
        else:
            checks.append(
                DoctorCheck(name="mcp-oauth", passed=True, detail="no MCP OAuth servers named")
            )

        is_git = (cwd / ".git").is_dir()
        checks.append(
            DoctorCheck(
                name="working-directory",
                passed=is_git,
                detail=(
                    f"{cwd} is a git repository" if is_git else f"{cwd} is NOT a git repository"
                ),
            )
        )

        return DoctorReport(
            checks=tuple(checks),
            auth_mode=auth_mode,
            probe_strategies=strategies,
        )

    def _codex_version(self, path: str) -> str | None:
        try:
            result = self._run([path, "--version"], timeout=10)
        except (OSError, subprocess.TimeoutExpired):
            return None
        if result.returncode != 0:
            return None
        text = (result.stdout or result.stderr or "").strip()
        return text or None

    def _version_meets_floor(self, version_text: str | None) -> bool:
        if version_text is None:
            return False
        match = _VERSION_RE.search(version_text)
        if match is None:
            return False
        parsed = (int(match.group(1)), int(match.group(2)), int(match.group(3)))
        return parsed >= self._minimum

    def _login_status_ok(self, path: str) -> bool:
        try:
            result = self._run([path, "login", "status"], timeout=10)
        except (OSError, subprocess.TimeoutExpired):
            return False
        return result.returncode == 0

    def _exec_help_has_flags(self, path: str) -> bool:
        try:
            result = self._run([path, "exec", "--help"], timeout=10)
        except (OSError, subprocess.TimeoutExpired):
            return False
        text = f"{result.stdout}\n{result.stderr}"
        return all(flag in text for flag in _REQUIRED_EXEC_FLAGS)

    def _auth_mode(self) -> str:
        if self._environ.get("OPENAI_API_KEY") or self._environ.get("CODEX_API_KEY"):
            return "api_key"
        auth = self._home / ".codex" / "auth.json"
        if auth.is_file():
            return "chatgpt_plan"
        return "none"

    def _probe_app_server_live(self) -> bool:
        """Return True when ``codex app-server --help`` succeeds (cheap live probe)."""
        codex = self._which("codex")
        if codex is None:
            return False
        try:
            result = self._run([codex, "app-server", "--help"], timeout=10)
        except (OSError, subprocess.TimeoutExpired):
            return False
        if result.returncode != 0:
            return False
        text = f"{result.stdout}\n{result.stderr}".lower()
        return "stdio" in text or "app-server" in text


def _default_run(
    argv: Sequence[str],
    *,
    timeout: float = 10,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # nosec B603
        list(argv),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


__all__ = [
    "CodexDoctorEnvironment",
    "MINIMUM_CODEX_VERSION",
]
