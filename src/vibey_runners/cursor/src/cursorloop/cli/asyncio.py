# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The single anyio bridge between Typer sync commands and async runner I/O.

SIGTERM is remapped to SIGINT so both signals raise KeyboardInterrupt and
``finally`` blocks (hooks restore, lock release, gateway close) still run.
"""

from __future__ import annotations

import functools
import os
import signal
import sys
from collections.abc import Awaitable, Callable

import anyio


def _sigterm_as_sigint(signum: int, frame: object) -> None:
    del signum, frame
    os.kill(os.getpid(), signal.SIGINT)


def async_command[**P, R](func: Callable[P, Awaitable[R]]) -> Callable[P, R]:
    """Wrap an async Typer command body so Typer (sync) can call it directly."""

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        previous_handler = None
        if hasattr(signal, "SIGTERM"):  # pragma: no cover - platform-dependent
            previous_handler = signal.signal(signal.SIGTERM, _sigterm_as_sigint)
        bound = functools.partial(func, *args, **kwargs)
        try:
            return anyio.run(bound)
        except KeyboardInterrupt:  # pragma: no cover - real Ctrl-C not in unit tests
            print("\nInterrupted — shutting down gracefully.", file=sys.stderr)
            raise SystemExit(130) from None
        finally:
            if previous_handler is not None:  # pragma: no cover - platform-dependent
                signal.signal(signal.SIGTERM, previous_handler)

    return wrapper
