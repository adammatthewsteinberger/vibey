# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Pure formatting for git savepoint commit subjects and bodies."""

from __future__ import annotations

_SUBJECT_MAX = 72


def format_savepoint_commit_message(
    *,
    run_id: str,
    attempt: int,
    verdict_name: str,
    summary: str,
    remaining_work: tuple[str, ...],
    changed_paths: tuple[str, ...],
    label: str,
) -> tuple[str, str]:
    """Return (subject, body) using Conventional Commits.

    Subject: ``chore(claudeloop): turn {n} — {headline}``
    Headline preference: first summary line → first path basename → fallback.
    """
    headline = _headline(summary=summary, changed_paths=changed_paths)
    subject = f"chore(claudeloop): turn {attempt} — {headline}"
    if len(subject) > _SUBJECT_MAX:
        subject = subject[: _SUBJECT_MAX - 1].rstrip() + "…"

    remaining_lines = (
        "\n".join(f"- {item}" for item in remaining_work) if remaining_work else "- (none)"
    )
    path_lines = "\n".join(f"- {path}" for path in changed_paths) if changed_paths else "- (none)"
    summary_block = summary.strip() if summary.strip() else "(none)"
    body = (
        f"Run: {run_id}\n"
        f"Attempt: {attempt}\n"
        f"Verdict: {verdict_name}\n"
        f"Label: {label}\n"
        f"\n"
        f"Summary:\n{summary_block}\n"
        f"\n"
        f"Remaining work:\n{remaining_lines}\n"
        f"\n"
        f"Changed paths:\n{path_lines}\n"
    )
    return subject, body


def _headline(*, summary: str, changed_paths: tuple[str, ...]) -> str:
    for line in summary.splitlines():
        cleaned = line.strip()
        if cleaned:
            return cleaned
    if changed_paths:
        name = changed_paths[0].rstrip("/").rsplit("/", 1)[-1]
        if name:
            return name
    return "workspace checkpoint"
