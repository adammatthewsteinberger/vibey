# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Output formatting shared by CLI commands."""

from __future__ import annotations

from agyloop.application.usecases.doctor import DoctorCheck
from agyloop.domain.classify import Classification
from agyloop.domain.session import SessionRef


def render_doctor_checks(checks: list[DoctorCheck]) -> str:
    lines = []
    for check in checks:
        mark = "ok" if check.passed else "FAIL"
        lines.append(f"  [{mark}] {check.name}: {check.detail}")
    lines.append("Live quota is not readable from this CLI — check AI Studio / Cloud Console.")
    return "\n".join(lines)


def render_classification(result: Classification) -> str:
    state = result.state
    extra = ""
    rate = getattr(state, "rate_limit_type", None)
    if rate:
        extra = f" rate_limit_type={rate}"
    resets = getattr(state, "resets_at", None)
    if resets is not None:
        extra += f" resets_at={resets.isoformat()}"
    return f"rung={result.rung} state={type(state).__name__}{extra}"


def render_session_list(sessions: list[SessionRef]) -> str:
    if not sessions:
        return (
            "No agyloop runs found under .agyloop/runs/. "
            "This listing is the local registry only; vendor conversations "
            "cannot be enumerated."
        )
    lines = ["agyloop run registry (not vendor conversations — those cannot be enumerated):"]
    for ref in sessions:
        modified = ref.last_modified.isoformat() if ref.last_modified else "unknown"
        preview = f"  {ref.first_prompt_preview}" if ref.first_prompt_preview else ""
        lines.append(f"  {ref.session_id}  {modified}  {ref.cwd}{preview}")
    return "\n".join(lines)
