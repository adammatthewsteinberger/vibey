# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""App-server rate-limit probe: handshake, graceful degradation, never-consume."""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from codexloop.domain.capacity import PlanWindows
from codexloop.infrastructure.appserver.client import DEFAULT_ARGV, AppServerClient
from tests.application.fakes import FakeLogger

SHIM = Path(__file__).resolve().parents[1] / "shim" / "fake_appserver.py"
CONSUME = "account/rateLimitResetCredit/consume"
RATE_LIMITS = "account/rateLimits/read"
NOW = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)

INITIALIZE = {
    "id": 1,
    "method": "initialize",
    "params": {
        "clientInfo": {"name": "codexloop", "title": "codexloop", "version": "0.1.0"},
        "capabilities": {"experimentalApi": True},
    },
}
INITIALIZED = {"method": "initialized", "params": {}}
READ_RATE_LIMITS = {"id": 2, "method": RATE_LIMITS}


def _shim_argv() -> list[str]:
    return [sys.executable, str(SHIM)]


def _client(
    tmp_path: Path,
    *,
    mode: str = "ok",
    logger: FakeLogger | None = None,
    timeout: float = 2.0,
) -> AppServerClient:
    env = {
        **os.environ,
        "FAKE_APPSERVER_MODE": mode,
        "FAKE_APPSERVER_LOG": str(tmp_path / "appserver.jsonl"),
    }
    return AppServerClient(
        argv=_shim_argv(),
        cwd=tmp_path,
        env=env,
        timeout=timeout,
        logger=logger,
        now=NOW,
    )


def _recorded(tmp_path: Path) -> list[dict[str, object]]:
    path = tmp_path / "appserver.jsonl"
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _methods(messages: list[dict[str, object]]) -> list[str]:
    return [str(msg["method"]) for msg in messages if "method" in msg]


def test_default_argv_is_codex_app_server_stdio() -> None:
    assert DEFAULT_ARGV == ["codex", "app-server", "--stdio"]


async def test_handshake_sends_initialize_initialized_then_rate_limits_read(
    tmp_path: Path,
) -> None:
    windows = await _client(tmp_path).read_rate_limits()

    messages = _recorded(tmp_path)
    assert messages == [INITIALIZE, INITIALIZED, READ_RATE_LIMITS]
    for message in messages:
        assert "jsonrpc" not in message
    initialize_params = messages[0]["params"]
    assert isinstance(initialize_params, dict)
    capabilities = initialize_params["capabilities"]
    assert isinstance(capabilities, dict)
    assert capabilities["experimentalApi"] is True

    assert isinstance(windows, PlanWindows)
    assert windows.plan_type == "plus"
    assert windows.limit_reached is None
    assert windows.primary is not None
    assert windows.primary.used_percent == 0.0
    assert windows.primary.window_minutes == 299
    assert windows.primary.resets_at == NOW + timedelta(seconds=17940)
    assert windows.secondary is not None
    assert windows.secondary.used_percent == 6.0
    assert windows.secondary.window_minutes == 10079
    assert windows.secondary.resets_at == NOW + timedelta(seconds=275281)


async def test_method_not_found_returns_none(tmp_path: Path) -> None:
    assert await _client(tmp_path, mode="method_not_found").read_rate_limits() is None


async def test_missing_capability_returns_none_and_logs_one_warning(tmp_path: Path) -> None:
    logger = FakeLogger()
    result = await _client(tmp_path, mode="missing_capability", logger=logger).read_rate_limits()
    assert result is None
    warnings = [(event, kwargs) for level, event, kwargs in logger.events if level == "warning"]
    assert len(warnings) == 1
    event, kwargs = warnings[0]
    assert "experimental" in event.lower() or "capability" in event.lower()
    assert kwargs == {} or isinstance(kwargs, dict)


async def test_malformed_response_returns_none(tmp_path: Path) -> None:
    assert await _client(tmp_path, mode="malformed").read_rate_limits() is None


async def test_spawn_failure_returns_none(tmp_path: Path) -> None:
    client = AppServerClient(
        argv=[str(tmp_path / "no-such-codex-app-server")],
        cwd=tmp_path,
        env={},
        timeout=1.0,
    )
    assert await client.read_rate_limits() is None


async def test_request_timeout_returns_none(tmp_path: Path) -> None:
    assert await _client(tmp_path, mode="hang", timeout=0.2).read_rate_limits() is None


async def test_consume_is_never_called(tmp_path: Path) -> None:
    await _client(tmp_path).read_rate_limits()
    methods = _methods(_recorded(tmp_path))
    assert CONSUME not in methods
    assert RATE_LIMITS in methods
    assert methods == ["initialize", "initialized", RATE_LIMITS]
