# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Registry of generated ``agyloop api`` command paths (drift gate)."""

from __future__ import annotations

from agyloop.infrastructure.api.discover import ApiLane

REGISTERED_COMMAND_PATHS: set[str] = set()
REGISTERED_VERTEX_PATHS: set[str] = set()


def register_command_path(path: str, *, lane: ApiLane = "developer") -> None:
    if lane == "vertex":
        REGISTERED_VERTEX_PATHS.add(path)
    else:
        REGISTERED_COMMAND_PATHS.add(path)


def clear_registry() -> None:
    REGISTERED_COMMAND_PATHS.clear()
    REGISTERED_VERTEX_PATHS.clear()
