# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Single ``anyio.run()`` bridge: signals, drain, and exit-code translation."""

from __future__ import annotations

import asyncio
import signal
from collections.abc import Callable, Coroutine
from functools import wraps
from typing import Any

import anyio
import typer

from codexloop.application.dto import RunResult
from codexloop.bootstrap import DrainControl, current_drain, register_drain
from codexloop.domain.errors import ConfigurationError


def sysexit_for(result: RunResult) -> int:
    if result.reason == "stop":
        return 130
    if result.reason.startswith("wind-down"):
        return 75  # EX_TEMPFAIL — signals handoff to supervisor
    if result.success:
        return 0
    return 1


def _request_drain() -> None:
    drain = current_drain()
    if drain is not None:
        drain.request_stop()


def _signal_handler(_signum: int, _frame: object | None) -> None:
    _request_drain()


def _install_drain_signals() -> None:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        signal.signal(signal.SIGINT, _signal_handler)
        signal.signal(signal.SIGTERM, _signal_handler)
        return
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _request_drain)
        except (NotImplementedError, RuntimeError):
            signal.signal(sig, _signal_handler)


def _raise_for_result(result: object) -> None:
    if not isinstance(result, RunResult):
        return
    code = sysexit_for(result)
    if code != 0:
        raise typer.Exit(code)


def async_command[**P, T](func: Callable[P, Coroutine[Any, Any, T]]) -> Callable[P, T]:
    """Run an async Typer command via ``anyio.run()`` with SIGINT/SIGTERM drain."""

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        async def _runner() -> T:
            register_drain(DrainControl())
            _install_drain_signals()
            return await func(*args, **kwargs)

        try:
            result = anyio.run(_runner)
        except ConfigurationError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(2) from exc
        except KeyboardInterrupt:
            _request_drain()
            raise typer.Exit(130) from None
        _raise_for_result(result)
        return result

    return wrapper
