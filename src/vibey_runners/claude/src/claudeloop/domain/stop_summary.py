# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Pure assembly of the mid-run stop summary markdown document."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StopSummaryInput:
    run_id: str
    session_id: str | None
    reason: str
    turns_spent: int
    dollars_spent: float
    last_summary: str
    remaining_plan_items: tuple[str, ...]
    remaining_work: tuple[str, ...]
    git_changes: str
    latest_savepoint: str | None
    events_path: str
    resume_hint: str


def render_stop_summary(data: StopSummaryInput) -> str:
    remaining_plan = (
        "\n".join(f"- [ ] {item}" for item in data.remaining_plan_items)
        if data.remaining_plan_items
        else "_No checklist items remaining (or plan had no checkboxes)._"
    )
    remaining_work = (
        "\n".join(f"- {item}" for item in data.remaining_work)
        if data.remaining_work
        else "_No structured remaining_work reported on the last turn._"
    )
    savepoint = data.latest_savepoint or "_No save points created yet._"
    changes = data.git_changes.strip() or "_No git changes detected for this run._"
    session = data.session_id or "_unknown_"

    return (
        f"# Claudeloop stop summary — `{data.run_id}`\n\n"
        f"**Reason:** {data.reason}\n\n"
        f"**Session:** `{session}`\n\n"
        f"**Turns spent:** {data.turns_spent} · **Dollars spent:** "
        f"{data.dollars_spent:.4f}\n\n"
        f"## Last agent summary\n\n{data.last_summary or '_none_'}\n\n"
        f"## Changes during this session\n\n```\n{changes}\n```\n\n"
        f"## Remaining plan checklist\n\n{remaining_plan}\n\n"
        f"## Remaining work (structured)\n\n{remaining_work}\n\n"
        f"## What's next\n\n{data.resume_hint}\n\n"
        f"## Latest save point\n\n{savepoint}\n\n"
        f"## Logs\n\nTail events with:\n\n"
        f"```bash\nclaudeloop logs --run-id {data.run_id} --follow\n```\n\n"
        f"Events file: `{data.events_path}`\n"
    )
