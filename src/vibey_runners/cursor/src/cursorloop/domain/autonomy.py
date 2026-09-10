# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Autonomy preamble: never block on a human, always emit a verdict fence."""

from __future__ import annotations

from cursorloop.domain.completion import DEFAULT_DONE_MARKER, VERDICT_FENCE

VERDICT_SCHEMA_DESCRIPTION = (
    "Per-turn completion verdict JSON object. "
    "Fields: complete (boolean; true only when the entire task is finished), "
    "remaining_work (array of strings; concrete unfinished items, including "
    "waitable background jobs, tests, or builds you started), "
    "blocked_on (string or null; set ONLY for a true external or human blocker "
    "such as missing credentials or a required human decision — MUST be null "
    "when waiting on work you started yourself; waitable items belong in "
    "remaining_work), "
    "summary (string; short status of this turn). "
    "A non-null blocked_on immediately stops the autonomous run as failed."
)


def autonomy_preamble(done_marker: str = DEFAULT_DONE_MARKER, require_verdict: bool = False) -> str:
    """Return the constant unattended-run instructions for the model.

    No human is available. Choose the option you would recommend, state the
    assumption inline, and proceed. Never ask a clarifying question. End every
    turn with the verdict fence. ``blocked_on`` is only for true external blockers.
    """
    require_clause = ""
    if require_verdict:
        require_clause = (
            f" The `{VERDICT_FENCE}` fence is required on every turn; consecutive "
            "turns without a well-formed verdict are treated as blocked."
        )
    return (
        "You are running autonomously and unattended. No human is available to "
        "answer a question mid-task. Nobody is watching this session in real "
        "time. Never end a turn by asking a clarifying question or waiting for "
        "confirmation on a reversible action that follows from the task — just "
        "do it. If you would normally ask, choose the option you would "
        "recommend, state the assumption inline, and proceed. "
        f"End every turn with a fenced `{VERDICT_FENCE}` block containing the "
        "verdict object described below. "
        "blocked_on is only for true external blockers (missing credentials, "
        "unpaid billing, a required human decision, unavailable MCP auth); "
        "waitable self-started work belongs in remaining_work with blocked_on "
        "null. "
        f"If you cannot emit a verdict block, include the marker "
        f"{done_marker} only when the entire task is finished."
        f"{require_clause}\n\n{VERDICT_SCHEMA_DESCRIPTION}"
    )
