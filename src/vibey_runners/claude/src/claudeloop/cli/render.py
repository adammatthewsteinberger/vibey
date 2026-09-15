# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Output formatting shared by CLI commands."""

from __future__ import annotations

from claudeloop.application.usecases.doctor import DoctorCheck
from claudeloop.domain.session import SessionRef


def render_doctor_checks(checks: list[DoctorCheck]) -> str:
    lines = []
    for check in checks:
        mark = "✓" if check.passed else "✗"
        lines.append(f"  {mark} {check.name}: {check.detail}")
    return "\n".join(lines)


def render_session_list(sessions: list[SessionRef]) -> str:
    if not sessions:
        return "No sessions found."
    lines = []
    for ref in sessions:
        branch = f" [{ref.git_branch}]" if ref.git_branch else ""
        modified = ref.last_modified.isoformat() if ref.last_modified else "unknown"
        lines.append(f"  {ref.session_id}  {modified}{branch}  {ref.cwd}")
    return "\n".join(lines)


def render_session_warning(ref: SessionRef, cwd: str) -> str:
    bar = "!" * 78
    lines = [
        bar,
        "WARNING: no prompt file and no --session-id given.",
        f"Auto-selected the MOST RECENT Claude Code session for directory: {cwd}",
        "",
        f"  session id      : {ref.session_id}",
        f"  last modified   : {ref.last_modified}",
    ]
    if ref.git_branch:
        lines.append(f"  git branch      : {ref.git_branch}")
    if ref.first_prompt_preview:
        lines.append(f"  first prompt    : {ref.first_prompt_preview}")
    lines += [
        "",
        "If this is NOT the session you meant to resume: stop now (Ctrl-C).",
        bar,
    ]
    return "\n".join(lines)
