# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Use case: wrap a prompt with the done-marker instruction used to detect
task completion across multi-turn autonomous runs.

``done_marker`` has no default here (unlike claudeloop's and agyloop's own
copies of this function): each runner's default marker string is a
vendor-specific domain constant (e.g. ``CLAUDELOOP_TASK_FULLY_COMPLETE`` vs
``AGYLOOP_TASK_FULLY_COMPLETE``), so a shared default would silently pick
one runner's vocabulary for all of them. Callers pass their own runner's
``domain.completion.DEFAULT_DONE_MARKER`` explicitly.
"""

from __future__ import annotations

_DONE_INSTRUCTION_TEMPLATE = (
    "{prompt}\n\n"
    "---\n"
    "Process note (from the automation running you, not the user): this session "
    "may be resumed automatically across multiple turns if you get cut off. "
    "If, and only if, the ENTIRE task above is now fully complete with nothing "
    "left to do, end your final message with this exact line on its own: "
    "{marker}\n"
    "If any work remains -- including work you were mid-way through -- do NOT "
    "include that line, so the automation knows to resume you."
)


def with_done_marker_instruction(prompt_text: str, done_marker: str) -> str:
    """Ported from legacy/claude_autoresume.py's with_done_marker_instruction()
    as the fallback path for models without structured output."""
    return _DONE_INSTRUCTION_TEMPLATE.format(prompt=prompt_text, marker=done_marker)
