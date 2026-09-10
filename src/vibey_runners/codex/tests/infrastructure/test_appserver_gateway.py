# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""App-server AgentGateway: thread/turn RPCs, interrupt/steer, auto-approve."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import anyio

from codexloop.infrastructure.appserver.gateway import (
    CodexAppServerGateway,
    _PendingTurn,
    probe_app_server_transport,
)

SHIM = Path(__file__).resolve().parents[1] / "shim" / "fake_appserver.py"


def _argv() -> list[str]:
    return [sys.executable, str(SHIM)]


def _gateway(tmp_path: Path, *, mode: str = "ok") -> CodexAppServerGateway:
    env = {
        **os.environ,
        "FAKE_APPSERVER_MODE": mode,
        "FAKE_APPSERVER_LOG": str(tmp_path / "appserver.jsonl"),
    }
    return CodexAppServerGateway(
        cwd=tmp_path,
        argv=_argv(),
        env=env,
        timeout=5.0,
    )


def _methods(tmp_path: Path) -> list[str]:
    path = tmp_path / "appserver.jsonl"
    if not path.is_file():
        return []
    out: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        msg = json.loads(line)
        if isinstance(msg, dict) and "method" in msg:
            out.append(str(msg["method"]))
    return out


async def _wait_for_method(tmp_path: Path, method: str) -> None:
    with anyio.fail_after(1):
        while method not in _methods(tmp_path):
            await anyio.sleep(0.01)


async def test_send_turn_starts_thread_and_completes(tmp_path: Path) -> None:
    gw = _gateway(tmp_path)
    try:
        outcome = await gw.send_turn("hi")
        assert outcome.thread_id == "thread-1"
        assert outcome.signals is not None
        assert outcome.signals.completed is True
        assert outcome.signals.final_message == "hello-from-appserver"
        await _wait_for_method(tmp_path, "approval/respond")
        methods = _methods(tmp_path)
        assert "initialize" in methods
        assert "thread/start" in methods
        assert "approval/respond" in methods
    finally:
        await gw.close()


async def test_second_turn_uses_turn_start(tmp_path: Path) -> None:
    gw = _gateway(tmp_path)
    try:
        await gw.send_turn("one")
        outcome = await gw.send_turn("two")
        assert outcome.signals is not None
        assert outcome.signals.final_message == "hello-again"
        assert "turn/start" in _methods(tmp_path)
    finally:
        await gw.close()


async def test_interrupt_and_steer_issue_rpcs(tmp_path: Path) -> None:
    gw = _gateway(tmp_path)
    try:
        await gw._ensure_session()  # noqa: SLF001 — exercise RPC helpers
        gw._pending = _PendingTurn(turn_id="turn-1")  # noqa: SLF001
        await gw.interrupt_turn()
        await gw.steer_turn("nudge")
        methods = _methods(tmp_path)
        assert "turn/interrupt" in methods
        assert "turn/steer" in methods
    finally:
        await gw.close()


async def test_probe_fallback_reason_on_init_fail(tmp_path: Path) -> None:
    env = {
        **os.environ,
        "FAKE_APPSERVER_MODE": "init_fail",
        "FAKE_APPSERVER_LOG": str(tmp_path / "appserver.jsonl"),
    }
    gateway, reason = await probe_app_server_transport(
        cwd=tmp_path,
        argv=_argv(),
        env=env,
    )
    assert gateway is None
    assert reason is not None
    assert "falling back to exec" in reason


async def test_probe_success(tmp_path: Path) -> None:
    env = {
        **os.environ,
        "FAKE_APPSERVER_MODE": "ok",
        "FAKE_APPSERVER_LOG": str(tmp_path / "appserver.jsonl"),
    }
    gateway, reason = await probe_app_server_transport(
        cwd=tmp_path,
        argv=_argv(),
        env=env,
    )
    assert reason is None
    assert gateway is not None
    await gateway.close()


async def test_send_turn_failed_notification(tmp_path: Path) -> None:
    gw = _gateway(tmp_path, mode="turn_fail")
    try:
        outcome = await gw.send_turn("hi")
        assert outcome.signals is not None
        assert outcome.signals.failed is True
        assert outcome.signals.error_code == "insufficient_quota"
    finally:
        await gw.close()


async def test_permission_profile_and_close(tmp_path: Path) -> None:
    from codexloop.application.ports import PermissionMode
    from codexloop.domain.model_profile import ModelEffortProfile

    gw = _gateway(tmp_path)
    try:
        await gw.set_profile(ModelEffortProfile.medium(model="gpt-test"))
        await gw.set_permission_mode(PermissionMode.READ_ONLY)
        await gw.set_permission_mode(PermissionMode.FULL_ACCESS)
        await gw.set_permission_mode(PermissionMode.AUTONOMOUS)
        await gw.set_cwd(str(tmp_path))
        await gw.set_session_resources(
            {"approval_policy": "on-request", "sandbox_mode": "read-only"}
        )
        assert gw._approval.value == "on-request"  # noqa: SLF001
        assert gw._sandbox.value == "read-only"  # noqa: SLF001
        await gw.set_session_resources({})
        assert gw.resolve_tool_approval("x", allow=True) is True
        await gw.close()
        await gw.close()  # idempotent
    finally:
        await gw.close()


async def test_interrupt_steer_noop_without_pending(tmp_path: Path) -> None:
    gw = _gateway(tmp_path)
    try:
        await gw.interrupt_turn()
        await gw.steer_turn("x")
        assert "turn/interrupt" not in _methods(tmp_path)
    finally:
        await gw.close()


async def test_handle_notification_variants(tmp_path: Path) -> None:
    gw = _gateway(tmp_path)
    gw._pending = _PendingTurn()  # noqa: SLF001
    assert await gw._handle_notification({"method": 1}) is False  # noqa: SLF001
    assert await gw._handle_notification({"method": "unknown"}) is False  # noqa: SLF001
    assert (
        await gw._handle_notification(  # noqa: SLF001
            {"method": "turn.started", "params": {"turnId": "t9"}}
        )
        is True
    )
    assert gw._pending.turn_id == "t9"  # noqa: SLF001
    await gw._handle_notification(  # noqa: SLF001
        {"method": "turn/outputDelta", "params": {"text": "ab"}}
    )
    assert gw._pending.final_message == "ab"  # noqa: SLF001
    await gw._handle_notification(  # noqa: SLF001
        {"method": "turn.completed", "params": {"message": "done"}}
    )
    assert gw._pending.completed is True  # noqa: SLF001
    assert gw._pending.final_message == "done"  # noqa: SLF001
    gw._pending = _PendingTurn()  # noqa: SLF001
    await gw._handle_notification({"method": "turn.failed", "params": {}})  # noqa: SLF001
    assert gw._pending.failed is True  # noqa: SLF001
    assert gw._pending.error_code == "turn_failed"  # noqa: SLF001


async def test_rpc_error_and_blank_line_reader(tmp_path: Path) -> None:
    from codexloop.infrastructure.appserver.gateway import _LineReader, _rpc_error

    assert _rpc_error({"error": {"code": 1}}) == {"code": 1}
    assert _rpc_error({"error": "boom"}) == {"message": "boom"}
    assert _rpc_error({}) is None

    class _Stream:
        def __init__(self, chunks: list[bytes]) -> None:
            self._chunks = list(chunks)

        async def receive(self, _n: int) -> bytes:
            if not self._chunks:
                from anyio import EndOfStream

                raise EndOfStream
            return self._chunks.pop(0)

    reader = _LineReader(_Stream([b"\n", b'{"id":1,"result":{}}\n']))  # type: ignore[arg-type]
    assert await reader.read_line() == {"id": 1, "result": {}}
    assert await reader.read_line() is None
