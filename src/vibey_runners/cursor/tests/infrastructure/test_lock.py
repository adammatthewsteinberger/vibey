# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from pathlib import Path

from cursorloop.infrastructure.lock import FileAgentLock


def test_exclusive_acquire_per_agent(tmp_path: Path) -> None:
    lock_a = FileAgentLock(tmp_path / ".cursorloop" / "locks")
    lock_b = FileAgentLock(tmp_path / ".cursorloop" / "locks")
    assert lock_a.acquire("agent-1") is True
    assert lock_b.acquire("agent-1") is False
    lock_a.release("agent-1")
    assert lock_b.acquire("agent-1") is True
    lock_b.release("agent-1")


def test_different_agents_do_not_contend(tmp_path: Path) -> None:
    lock = FileAgentLock(tmp_path / ".cursorloop" / "locks")
    assert lock.acquire("agent-a") is True
    assert lock.acquire("agent-b") is True
    lock.release("agent-a")
    lock.release("agent-b")
