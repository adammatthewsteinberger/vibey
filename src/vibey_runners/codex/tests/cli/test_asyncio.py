# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Unit coverage for CLI asyncio bridge helpers."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
import typer

from codexloop.cli import asyncio as cli_asyncio
from codexloop.domain.errors import ConfigurationError


def test_request_drain_noop_without_drain(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli_asyncio, "current_drain", lambda: None)
    cli_asyncio._request_drain()


def test_signal_handler_requests_drain(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[int] = []
    monkeypatch.setattr(cli_asyncio, "_request_drain", lambda: calls.append(1))
    cli_asyncio._signal_handler(2, None)
    assert calls == [1]


def test_install_drain_signals_without_running_loop(monkeypatch: pytest.MonkeyPatch) -> None:
    installed: list[object] = []

    def fake_signal(sig: object, handler: object) -> None:
        installed.append((sig, handler))

    monkeypatch.setattr(cli_asyncio.signal, "signal", fake_signal)

    def boom() -> object:
        raise RuntimeError("no loop")

    monkeypatch.setattr(cli_asyncio.asyncio, "get_running_loop", boom)
    cli_asyncio._install_drain_signals()
    assert len(installed) == 2


def test_install_drain_signals_falls_back_when_add_handler_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    installed: list[object] = []

    class _Loop:
        def add_signal_handler(self, *_a: object, **_k: object) -> None:
            raise NotImplementedError

    monkeypatch.setattr(cli_asyncio.asyncio, "get_running_loop", lambda: _Loop())
    monkeypatch.setattr(
        cli_asyncio.signal,
        "signal",
        lambda sig, handler: installed.append((sig, handler)),
    )
    cli_asyncio._install_drain_signals()
    assert len(installed) == 2


def test_async_command_configuration_error(monkeypatch: pytest.MonkeyPatch) -> None:
    @cli_asyncio.async_command
    async def boom() -> None:
        raise ConfigurationError("bad config")

    monkeypatch.setattr(cli_asyncio, "_install_drain_signals", lambda: None)
    with pytest.raises(typer.Exit) as exc:
        boom()
    assert exc.value.exit_code == 2


def test_async_command_keyboard_interrupt(monkeypatch: pytest.MonkeyPatch) -> None:
    drained: list[int] = []

    @cli_asyncio.async_command
    async def boom() -> None:
        return None

    monkeypatch.setattr(cli_asyncio, "_install_drain_signals", lambda: None)
    monkeypatch.setattr(cli_asyncio, "_request_drain", lambda: drained.append(1))
    monkeypatch.setattr(
        cli_asyncio.anyio,
        "run",
        lambda *_a, **_k: (_ for _ in ()).throw(KeyboardInterrupt()),
    )
    with pytest.raises(typer.Exit) as exc:
        boom()
    assert exc.value.exit_code == 130
    assert drained == [1]


def test_raise_for_result_ignores_non_run_result() -> None:
    cli_asyncio._raise_for_result(SimpleNamespace())
