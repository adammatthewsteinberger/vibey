# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Destructive-command prevention guard (Milestone 9 task 9.2)."""

import re
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class BlockedMatch:
    command: str
    rule_id: str
    description: str


class DestructiveCommandBlocked(Exception):
    def __init__(self, match: BlockedMatch) -> None:
        super().__init__(
            f"Blocked destructive command [{match.rule_id}]: "
            f"'{match.command}' ({match.description})"
        )
        self.match = match


_DESTRUCTIVE_RULES: tuple[tuple[str, str, re.Pattern[str]], ...] = (
    (
        "GIT_HARD_RESET",
        "Destructive git hard reset loses uncommitted changes",
        re.compile(r"\bgit\s+reset\s+--hard\b", re.IGNORECASE),
    ),
    (
        "GIT_FORCE_PUSH",
        "Destructive git force push can overwrite upstream history",
        re.compile(
            r"\bgit\s+push\s+.*(--force|-f\b|--force-with-lease)",
            re.IGNORECASE,
        ),
    ),
    (
        "GIT_DELETE_MAIN",
        "Destructive git branch deletion on main or master",
        re.compile(
            r"\bgit\s+branch\s+(-D|-d)\s+(main|master)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "FS_ROOT_RM",
        "Destructive root / home recursive delete",
        re.compile(
            r"\brm\s+-(rf|fr|r|f)*\s*(/|/\*|~|~/|\*)\s*($|\s)",
            re.IGNORECASE,
        ),
    ),
    (
        "FS_MKFS",
        "Filesystem formatting command",
        re.compile(r"\b(mkfs(\.[a-z0-9]+)?)\s+", re.IGNORECASE),
    ),
    (
        "FS_RAW_DD",
        "Raw disk overwrite with dd",
        re.compile(r"\bdd\s+.*of=/dev/", re.IGNORECASE),
    ),
    (
        "FS_CHMOD_ROOT",
        "Recursive permission modification on root",
        re.compile(r"\bchmod\s+-R\s+[0-7]+\s+/\s*($|\s)", re.IGNORECASE),
    ),
    (
        "SYS_POWER",
        "System power / reboot command",
        re.compile(r"\b(shutdown|reboot|poweroff|init\s+[06])\b", re.IGNORECASE),
    ),
    (
        "SYS_FORK_BOMB",
        "Shell fork bomb pattern",
        re.compile(r":\(\)\s*\{\s*:\|:&\s*\};:", re.IGNORECASE),
    ),
    (
        "SQL_DROP_DATABASE",
        "Destructive SQL DROP DATABASE",
        re.compile(r"\bDROP\s+DATABASE\b", re.IGNORECASE),
    ),
    (
        "SQL_DROP_TABLE",
        "Destructive SQL DROP TABLE",
        re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
    ),
)


def scan_command(command: Sequence[str] | str) -> BlockedMatch | None:
    """Scans a command string or argv sequence against destructive rules."""
    cmd_str = command if isinstance(command, str) else " ".join(command)
    cmd_str = cmd_str.strip()

    for rule_id, desc, pattern in _DESTRUCTIVE_RULES:
        if pattern.search(cmd_str):
            return BlockedMatch(command=cmd_str, rule_id=rule_id, description=desc)
    return None


class CommandSecurityPolicy:
    """Security policy enforcement for commands executed in engine/worktree contexts."""

    def __init__(self) -> None:
        pass

    def is_allowed(self, command: Sequence[str] | str) -> bool:
        return scan_command(command) is None

    def check_command(self, command: Sequence[str] | str) -> None:
        match = scan_command(command)
        if match is not None:
            raise DestructiveCommandBlocked(match)
