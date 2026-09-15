# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Pure builders for the managed autonomy ``hooks.json`` fragment.

Cursor hooks are file-based only. These payloads are what generated scripts
emit on stdout. Exit 2 blocks the action — autonomy hooks exist to ALLOW, so
the success exit is 0 and these builders never produce a deny.
"""

from __future__ import annotations

MANAGED_EVENTS: tuple[str, ...] = (
    "preToolUse",
    "beforeShellExecution",
    "beforeMCPExecution",
    "beforeReadFile",
    "beforeSubmitPrompt",
    "stop",
)

HOOK_SUCCESS_EXIT = 0


def allow_payload(event: str) -> dict[str, str]:
    """Return the allow decision for a managed hook event.

    Never deny, never ask. Exit 2 is not represented here.
    """
    if event not in MANAGED_EVENTS:
        raise ValueError(f"unmanaged hook event: {event}")
    return {"permission": "allow"}


def preamble_injection_payload(preamble: str) -> dict[str, str]:
    """Payload for ``beforeSubmitPrompt`` to re-inject the autonomy preamble."""
    return {"additional_context": preamble, "permission": "allow"}
