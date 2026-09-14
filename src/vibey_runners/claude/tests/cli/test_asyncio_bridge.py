# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Tests for cli/asyncio.py — the async_command decorator and SIGTERM bridge."""

from __future__ import annotations

from claudeloop.cli.asyncio import _sigterm_as_sigint, async_command


class TestSigtermAsSigint:
    def test_sends_sigint(self) -> None:
        import os
        import signal
        from unittest.mock import patch

        with patch("os.kill") as mock_kill:
            _sigterm_as_sigint(15, None)
            mock_kill.assert_called_once_with(os.getpid(), signal.SIGINT)


class TestAsyncCommand:
    def test_wraps_async_function(self) -> None:
        async def greet(name: str) -> str:
            return f"hello {name}"

        sync_fn = async_command(greet)
        result = sync_fn("world")
        assert result == "hello world"

    def test_preserves_name(self) -> None:
        async def my_func() -> None:
            pass

        wrapped = async_command(my_func)
        assert wrapped.__name__ == "my_func"

    def test_returns_value(self) -> None:
        async def add(a: int, b: int) -> int:
            return a + b

        sync_fn = async_command(add)
        assert sync_fn(2, 3) == 5
