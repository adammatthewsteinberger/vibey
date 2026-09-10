# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

import signal
from unittest.mock import patch

from cursorloop.cli import asyncio as cli_asyncio
from cursorloop.cli.app import main


def test_main_returns_zero_on_clean_system_exit() -> None:
    with patch("cursorloop.cli.app.app", side_effect=SystemExit(None)):
        assert main() == 0


def test_main_returns_int_code_from_system_exit() -> None:
    with patch("cursorloop.cli.app.app", side_effect=SystemExit(7)):
        assert main() == 7


def test_main_returns_one_for_non_int_system_exit() -> None:
    with patch("cursorloop.cli.app.app", side_effect=SystemExit("nope")):
        assert main() == 1


def test_main_returns_zero_when_app_returns() -> None:
    with patch("cursorloop.cli.app.app", return_value=None):
        assert main() == 0


def test_sigterm_handler_forwards_sigint() -> None:
    with patch("cursorloop.cli.asyncio.os.kill") as kill:
        cli_asyncio._sigterm_as_sigint(signal.SIGTERM, None)
    kill.assert_called_once()
    assert kill.call_args.args[1] == signal.SIGINT
