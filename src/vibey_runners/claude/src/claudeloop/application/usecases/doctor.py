# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Use case: pre-flight checks before starting a long unattended run.

Deliberately checks BEFORE a run starts, not during — an MCP OAuth prompt or a
missing `claude` binary discovered three hours into an unattended run is much
worse than the same failure at `claudeloop doctor` time. See
docs/architecture/decisions/0007-ask-user-question-denied-with-guidance.md for
why MCP OAuth specifically can never be mitigated mid-run."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from claudeloop.application.interfaces import DoctorEnvironment


@dataclass(frozen=True, slots=True)
class DoctorCheck:
    name: str
    passed: bool
    detail: str


def run_doctor(env: DoctorEnvironment, *, cwd: Path) -> list[DoctorCheck]:
    checks: list[DoctorCheck] = []

    cli_path = env.find_claude_cli()
    if cli_path is None:
        checks.append(
            DoctorCheck(
                name="claude-cli",
                passed=False,
                detail="`claude` not found on PATH. Install Claude Code first.",
            )
        )
    else:
        version = env.claude_cli_version(cli_path)
        checks.append(
            DoctorCheck(
                name="claude-cli",
                passed=version is not None,
                detail=f"found at {cli_path} ({version or 'version unknown'})",
            )
        )

    authed = env.is_authenticated()
    checks.append(
        DoctorCheck(
            name="authentication",
            passed=authed,
            detail="credentials present" if authed else "no credentials found",
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
                    "MCP OAuth cannot complete unattended; verify these are already "
                    "authorized before starting a long run."
                ),
            )
        )
    else:
        checks.append(DoctorCheck(name="mcp-servers", passed=True, detail="none configured"))

    sdk_version = env.anthropic_sdk_version()
    checks.append(
        DoctorCheck(
            name="anthropic-sdk",
            passed=sdk_version is not None,
            detail=(
                f"anthropic {sdk_version}" if sdk_version else "anthropic package not importable"
            ),
        )
    )

    api_count = env.api_surface_method_count()
    if api_count is None:
        checks.append(
            DoctorCheck(
                name="api-surface",
                passed=False,
                detail="could not verify generated REST surface baseline",
            )
        )
    else:
        checks.append(
            DoctorCheck(
                name="api-surface",
                passed=True,
                detail=f"{api_count} SDK methods bound under `claudeloop api`",
            )
        )

    is_git_repo = (cwd / ".git").is_dir()
    checks.append(
        DoctorCheck(
            name="working-directory",
            passed=is_git_repo,
            detail=(
                f"{cwd} is a git repository"
                if is_git_repo
                else f"{cwd} is NOT a git repository — bypassing permissions here is riskier"
            ),
        )
    )

    return checks


def all_passed(checks: list[DoctorCheck]) -> bool:
    return all(c.passed for c in checks)
