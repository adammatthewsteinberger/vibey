# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Minimal run-state bus: read ``state.json`` for ``watch`` / status helpers."""

from __future__ import annotations

import json
from pathlib import Path


def read_state(path: Path) -> dict[str, object]:
    """Return parsed state.json, or ``{}`` if missing/invalid. Never raises."""
    try:
        if not path.is_file():
            return {}
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (OSError, json.JSONDecodeError):
        return {}
    return {}


def watch_state(path: Path) -> dict[str, object]:
    """Alias for :func:`read_state` — one-shot snapshot for ``watch``."""
    return read_state(path)


__all__ = ["read_state", "watch_state"]
