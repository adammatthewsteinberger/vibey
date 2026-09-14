# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Git save-point value objects — migration-like snapshots of the worktree."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class SavePointRef:
    n: int
    ref: str
    sha: str
    label: str
    at: datetime
    plan_item: str | None = None
    # True when create() wrote a new commit; False for ref-only unchanged trees.
    committed: bool = False

    def __post_init__(self) -> None:
        if self.n < 1:
            raise ValueError("save point number must be >= 1")
        if not self.ref.strip():
            raise ValueError("save point ref must not be blank")
        if not self.sha.strip():
            raise ValueError("save point sha must not be blank")


@dataclass(frozen=True, slots=True)
class UnwindResult:
    to: SavePointRef
    backup_ref: str | None
    restored_sha: str
