# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Workspace snapshot helper — copy tree excluding ``.codexloop/``."""

from __future__ import annotations

import shutil
from pathlib import Path

_SKIP = {".codexloop", ".git"}


def create_snapshot(*, cwd: Path, dest: Path) -> Path:
    """Copy ``cwd`` into ``dest``, skipping control-plane and ``.git`` dirs."""
    dest.mkdir(parents=True, exist_ok=True)
    for child in cwd.iterdir():
        if child.name in _SKIP:
            continue
        target = dest / child.name
        if child.is_dir():
            shutil.copytree(child, target, dirs_exist_ok=True)
        elif child.is_file():  # pragma: no branch
            shutil.copy2(child, target)
    return dest


def restore_snapshot(*, snapshot: Path, cwd: Path) -> None:
    """Restore files from ``snapshot`` into ``cwd`` (does not delete extras)."""
    if not snapshot.is_dir():
        raise FileNotFoundError(f"snapshot not found: {snapshot}")
    for child in snapshot.iterdir():
        target = cwd / child.name
        if child.is_dir():
            if target.exists():  # pragma: no branch
                shutil.rmtree(target)
            shutil.copytree(child, target)
        elif child.is_file():  # pragma: no branch
            shutil.copy2(child, target)


__all__ = ["create_snapshot", "restore_snapshot"]
