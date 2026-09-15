# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Use case: pre-flight checks before a long unattended run.

Resolves the Gemini auth lane and its source without guessing. Interactive
hooks must be absent. Live quota is not readable here.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agyloop.application.interfaces.doctor import (
    AuthLane,
    AuthResolution,
    DoctorEnvironment,
    HarnessStatus,
)


@dataclass(frozen=True, slots=True)
class DoctorCheck:
    name: str
    passed: bool
    detail: str


def run_doctor(env: DoctorEnvironment, *, cwd: Path) -> list[DoctorCheck]:
    checks: list[DoctorCheck] = []
    auth = env.resolve_auth()
    checks.append(
        DoctorCheck(
            name="authentication",
            passed=auth.authenticated,
            detail=(
                f"lane={auth.lane} source={auth.source} — {auth.detail}"
                if auth.authenticated
                else auth.detail
            ),
        )
    )
    hooks_present = env.interactive_hooks_registered()
    checks.append(
        DoctorCheck(
            name="interactive-hooks",
            passed=not hooks_present,
            detail=(
                "ToolConfirmationHook/AskQuestionHook must never be registered"
                if hooks_present
                else "no interactive hooks registered"
            ),
        )
    )
    cli_path = env.find_agy_cli()
    if cli_path is None:
        checks.append(
            DoctorCheck(
                name="agy-cli",
                passed=True,
                detail="agy CLI not on PATH (SDK gateway does not require it)",
            )
        )
    else:
        version = env.agy_cli_version(cli_path)
        checks.append(
            DoctorCheck(
                name="agy-cli",
                passed=True,
                detail=f"found at {cli_path} ({version or 'version unknown'})",
            )
        )
    mcp_servers = env.configured_mcp_servers()
    if mcp_servers:
        checks.append(
            DoctorCheck(
                name="mcp-servers",
                passed=False,
                detail=(
                    f"{len(mcp_servers)} MCP server(s) configured ({', '.join(mcp_servers)}) — "
                    "MCP OAuth cannot complete unattended"
                ),
            )
        )
    else:
        checks.append(DoctorCheck(name="mcp-servers", passed=True, detail="none configured"))
    is_git_repo = (cwd / ".git").is_dir()
    checks.append(
        DoctorCheck(
            name="working-directory",
            passed=is_git_repo,
            detail=(
                f"{cwd} is a git repository"
                if is_git_repo
                else f"{cwd} is NOT a git repository — unattended writes here are riskier"
            ),
        )
    )

    # Check SDK harness viability (for --gateway sdk) - advisory only
    harness_status = env.check_sdk_harness()
    checks.append(
        DoctorCheck(
            name="sdk-harness",
            passed=True,  # Advisory only - CLI gateway is always available
            detail=harness_status.detail,
        )
    )
    return checks


def all_passed(checks: list[DoctorCheck]) -> bool:
    return all(check.passed for check in checks)


# Re-exported for the same reason `application/ports.py` re-exports the
# interfaces package: the vocabulary moved, the import path should not break.
__all__ = [
    "AuthLane",
    "AuthResolution",
    "DoctorCheck",
    "DoctorEnvironment",
    "HarnessStatus",
    "run_doctor",
]
