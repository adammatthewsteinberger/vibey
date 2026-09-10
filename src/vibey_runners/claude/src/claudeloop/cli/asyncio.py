# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The single anyio bridge point between Typer's sync command functions and the
async claude_agent_sdk / AutonomousRunner call chain. One bridge, not one per
command — see docs/architecture/overview.md's async-bridge note.

SIGTERM is converted to SIGINT at the OS level before anyio.run() starts, so
both signals get the same well-understood handling: Python's default SIGINT
handler raises KeyboardInterrupt in the main thread, which anyio propagates
into the running task tree as a cancellation — letting in-flight `finally`
blocks (closing the AgentGateway, flushing the audit log) run before the
process exits, instead of dying mid-write."""

from __future__ import annotations

import functools
import os
import signal
import sys
from collections.abc import Awaitable, Callable
from typing import ParamSpec, TypeVar

import anyio

P = ParamSpec("P")
R = TypeVar("R")


def _sigterm_as_sigint(signum: int, frame: object) -> None:
    del signum, frame
    os.kill(os.getpid(), signal.SIGINT)


def async_command(func: Callable[P, Awaitable[R]]) -> Callable[P, R]:
    """Wrap an async Typer command body so Typer (sync) can call it directly."""

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        previous_handler = None
        if hasattr(signal, "SIGTERM"):  # pragma: no cover - platform-dependent
            previous_handler = signal.signal(signal.SIGTERM, _sigterm_as_sigint)
        bound = functools.partial(func, *args, **kwargs)
        try:
            return anyio.run(bound)
        except KeyboardInterrupt:  # pragma: no cover - real Ctrl-C/SIGTERM not exercised in tests
            print("\nInterrupted — shutting down gracefully.", file=sys.stderr)
            raise SystemExit(130) from None
        finally:
            if previous_handler is not None:  # pragma: no cover - platform-dependent
                signal.signal(signal.SIGTERM, previous_handler)

    return wrapper
