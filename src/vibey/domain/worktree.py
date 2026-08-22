# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Pure naming rules for BUILD work-item worktrees (M6 task 6.2).

No I/O here -- just the deterministic path/branch scheme the infrastructure
worktree manager uses, kept pure so it's trivially testable and so the
manager and any future caller (e.g. a status report) never disagree about
where a work item's worktree lives. Returns a relative path string rather
than a `pathlib.Path`: domain/ forbids pathlib (test_domain_purity.py), so
joining this onto a repo root is the infrastructure layer's job.
"""

import re

_ITEM_ID_RE = re.compile(r"^[a-z0-9][a-z0-9\-]{0,63}$")


def validate_item_id(item_id: str) -> None:
    if not _ITEM_ID_RE.match(item_id):
        raise ValueError(
            f"invalid work item id {item_id!r}: must be 1-64 chars, "
            "lowercase alphanumeric and hyphens, starting with alphanumeric"
        )


def worktree_subpath(cycle: int, item_id: str) -> str:
    validate_item_id(item_id)
    return f".vibey/worktrees/{cycle}/{item_id}"


def branch_name(cycle: int, item_id: str) -> str:
    validate_item_id(item_id)
    return f"vibey/{cycle}/{item_id}"
