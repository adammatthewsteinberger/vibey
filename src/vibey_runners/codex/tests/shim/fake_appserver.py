#!/usr/bin/env python3
# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Fake ``codex app-server --stdio`` for handshake and degradation tests."""

from __future__ import annotations

import json
import os
import sys

RATE_LIMITS_BLOB = {
    "primary": {
        "used_percent": 0.0,
        "window_minutes": 299,
        "resets_in_seconds": 17940,
    },
    "secondary": {
        "used_percent": 6.0,
        "window_minutes": 10079,
        "resets_in_seconds": 275281,
    },
    "plan_type": "plus",
    "rate_limit_reached_type": None,
}


def _log_path() -> str | None:
    return os.environ.get("FAKE_APPSERVER_LOG") or None


def _mode() -> str:
    return os.environ.get("FAKE_APPSERVER_MODE", "ok")


def _record(message: object) -> None:
    path = _log_path()
    if path is None:
        return
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(message, separators=(",", ":")) + "\n")
        handle.flush()


def _write(payload: object) -> None:
    sys.stdout.write(json.dumps(payload, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def _initialize_result(msg_id: object) -> None:
    _write(
        {
            "id": msg_id,
            "result": {
                "protocolVersion": "1",
                "serverInfo": {"name": "fake-appserver", "version": "0.0.0"},
            },
        }
    )


def _handle_rate_limits(msg_id: object, mode: str) -> None:
    if mode == "method_not_found":
        _write({"id": msg_id, "error": {"code": -32601, "message": "Method not found"}})
        return
    if mode == "missing_capability":
        _write(
            {
                "id": msg_id,
                "error": {
                    "code": -32000,
                    "message": "account/rateLimits/read requires experimentalApi capability",
                },
            }
        )
        return
    if mode == "malformed":
        sys.stdout.write("{{{not-json\n")
        sys.stdout.flush()
        return
    if mode == "hang":
        return
    _write({"id": msg_id, "result": RATE_LIMITS_BLOB})


def _emit_turn(message: str = "done") -> None:
    _write({"method": "turn/started", "params": {"turnId": "turn-1", "turn": {"id": "turn-1"}}})
    _write({"method": "approval/request", "params": {"requestId": "apr-1"}})
    _write({"method": "item/agentMessage/delta", "params": {"delta": message}})
    _write({"method": "turn/completed", "params": {"finalMessage": message}})


def main() -> int:
    mode = _mode()
    thread_id = "thread-1"
    for raw in sys.stdin:
        line = raw.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            _record({"_unparsed": line})
            continue
        _record(message)
        if not isinstance(message, dict):
            continue
        method = message.get("method")
        msg_id = message.get("id")
        if method == "initialize":
            if mode == "init_fail":
                _write({"id": msg_id, "error": {"code": -32000, "message": "nope"}})
                continue
            _initialize_result(msg_id)
            continue
        if method == "initialized":
            continue
        if method == "account/rateLimits/read":
            _handle_rate_limits(msg_id, mode)
            continue
        if method == "thread/start":
            _write({"id": msg_id, "result": {"thread": {"id": thread_id}}})
            if mode == "turn_fail":
                _write({"method": "turn/started", "params": {"turnId": "turn-1"}})
                _write(
                    {
                        "method": "turn/failed",
                        "params": {"code": "insufficient_quota", "type": "billing"},
                    }
                )
            else:
                _emit_turn("hello-from-appserver")
            continue
        if method == "turn/start":
            _write({"id": msg_id, "result": {"turn": {"id": "turn-1"}}})
            _emit_turn("hello-again")
            continue
        if method == "turn/interrupt":
            _write({"id": msg_id, "result": {"ok": True}})
            continue
        if method == "turn/steer":
            _write({"id": msg_id, "result": {"ok": True}})
            continue
        if method == "approval/respond":
            continue
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
