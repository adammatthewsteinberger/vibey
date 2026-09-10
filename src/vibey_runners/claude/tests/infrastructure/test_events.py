# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Tests for infrastructure/events.py — JsonlRunEventSink."""

from __future__ import annotations

import json
from pathlib import Path

from claudeloop.infrastructure.events import JsonlRunEventSink


def test_creates_parent_directories(tmp_path: Path) -> None:
    path = tmp_path / "deep" / "nested" / "events.jsonl"
    JsonlRunEventSink(path, run_id="r1")
    assert path.is_file()


def test_creates_file_if_not_exists(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    JsonlRunEventSink(path, run_id="r1")
    assert path.is_file()


def test_does_not_touch_already_existing_file(tmp_path: Path) -> None:
    """The `if not self._path.exists(): touch()` guard must skip touch()
    (and so leave prior content alone) when the events file already exists
    -- as happens when a sink is re-created for a resumed run."""
    path = tmp_path / "events.jsonl"
    path.write_text('{"pre-existing": true}\n', encoding="utf-8")
    JsonlRunEventSink(path, run_id="r1")
    assert path.read_text(encoding="utf-8") == '{"pre-existing": true}\n'


def test_emit_writes_jsonl_line(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    sink = JsonlRunEventSink(path, run_id="r1")
    sink.emit("test_event")
    lines = path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["run_id"] == "r1"
    assert entry["event_type"] == "test_event"
    assert "ts" in entry


def test_emit_with_payload(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    sink = JsonlRunEventSink(path, run_id="r1")
    sink.emit("data_event", {"key": "value"})
    entry = json.loads(path.read_text(encoding="utf-8").strip())
    assert entry["payload"]["key"] == "value"


def test_emit_redacts_secrets(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    sink = JsonlRunEventSink(path, run_id="r1")
    sink.emit("auth", {"api_key": "sk-secret123"})
    entry = json.loads(path.read_text(encoding="utf-8").strip())
    assert entry["payload"]["api_key"] == "***REDACTED***"


def test_bind_session_id(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    sink = JsonlRunEventSink(path, run_id="r1")
    sink.bind(session_id="sess-1")
    sink.emit("test")
    entry = json.loads(path.read_text(encoding="utf-8").strip())
    assert entry["session_id"] == "sess-1"


def test_bind_attempt_and_phase(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    sink = JsonlRunEventSink(path, run_id="r1")
    sink.bind(attempt=3, phase="running")
    sink.emit("test")
    entry = json.loads(path.read_text(encoding="utf-8").strip())
    assert entry["attempt"] == 3
    assert entry["phase"] == "running"


def test_bind_trace_and_turn_id(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    sink = JsonlRunEventSink(path, run_id="r1", trace_id="t0")
    sink.bind(trace_id="t1", turn_id="turn-5")
    sink.emit("test")
    entry = json.loads(path.read_text(encoding="utf-8").strip())
    assert entry["trace_id"] == "t1"
    assert entry["turn_id"] == "turn-5"


def test_emit_multiple_lines(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    sink = JsonlRunEventSink(path, run_id="r1")
    sink.emit("e1")
    sink.emit("e2")
    sink.emit("e3")
    lines = path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 3
    assert json.loads(lines[0])["event_type"] == "e1"
    assert json.loads(lines[2])["event_type"] == "e3"


def test_no_trace_id_omitted(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    sink = JsonlRunEventSink(path, run_id="r1")
    sink.emit("test")
    entry = json.loads(path.read_text(encoding="utf-8").strip())
    assert "trace_id" not in entry


def test_no_payload_omitted(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    sink = JsonlRunEventSink(path, run_id="r1")
    sink.emit("test")
    entry = json.loads(path.read_text(encoding="utf-8").strip())
    assert "payload" not in entry


def test_initial_trace_id(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    sink = JsonlRunEventSink(path, run_id="r1", trace_id="initial-trace")
    sink.emit("test")
    entry = json.loads(path.read_text(encoding="utf-8").strip())
    assert entry["trace_id"] == "initial-trace"
