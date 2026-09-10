# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Use cases: enqueue operator control commands via a port."""

from __future__ import annotations

from pathlib import Path

from codexloop.application.interfaces import ControlInbox
from codexloop.domain.control import ControlCommand


def enqueue_control(inbox: ControlInbox, command: ControlCommand) -> Path:
    """Enqueue ``command`` and return the path written."""
    return inbox.enqueue(command)


__all__ = ["ControlInbox", "enqueue_control"]
