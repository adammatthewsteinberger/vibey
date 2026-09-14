# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The single asyncio bridge between Typer's sync commands and async I/O.

One ``asyncio.run`` call site for the whole CLI — not one per command.
"""

from __future__ import annotations

import asyncio
import functools
from collections.abc import Awaitable, Callable


def async_command[**P, R](func: Callable[P, Awaitable[R]]) -> Callable[P, R]:
    """Wrap an async Typer command body so Typer (sync) can call it directly."""

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        async def _bound() -> R:
            return await func(*args, **kwargs)

        return asyncio.run(_bound())

    return wrapper
