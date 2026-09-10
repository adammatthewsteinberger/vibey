# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Registry of generated ``claudeloop api`` command paths (drift gate)."""

from __future__ import annotations

REGISTERED_COMMAND_PATHS: set[str] = set()


def register_command_path(path: str) -> None:
    REGISTERED_COMMAND_PATHS.add(path)


def clear_registry() -> None:
    REGISTERED_COMMAND_PATHS.clear()
