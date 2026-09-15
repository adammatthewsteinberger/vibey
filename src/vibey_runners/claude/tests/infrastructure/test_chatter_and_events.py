# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Events sink trace/turn binding and chatter helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from claudeloop.infrastructure.chatter_log import chatter_payload, summarize_tool
from claudeloop.infrastructure.events import JsonlRunEventSink
from claudeloop.infrastructure.stream_ui import dump_transcript, iter_event_records


def test_event_sink_includes_trace_and_turn(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    sink = JsonlRunEventSink(path, run_id="r1", trace_id="t1")
    sink.bind(turn_id="turn-a", attempt=2, phase="RUNNING")
    sink.emit("chatter.prompt", {"text": "hello"})
    records = list(iter_event_records(path))
    assert len(records) == 1
    assert records[0]["trace_id"] == "t1"
    assert records[0]["turn_id"] == "turn-a"
    assert records[0]["event_type"] == "chatter.prompt"


def test_chatter_payload_modes() -> None:
    assert chatter_payload("x", mode="off") is None
    summary = chatter_payload("hello world", mode="summary")
    assert summary is not None
    assert summary["text"] == "hello world"
    assert "preview" in summary
    assert summary["truncated"] is False
    long = "x" * 2000
    summary_long = chatter_payload(long, mode="summary")
    assert summary_long is not None
    assert summary_long["text"] == long
    assert len(summary_long["preview"]) < len(long)
    assert summary_long["preview_truncated"] is True
    full = chatter_payload("hello world", mode="full")
    assert full is not None
    assert full["text"] == "hello world"


def test_chatter_payload_summary_keeps_full_prompt_text() -> None:
    """Stream UI / events consumers need the full prompt; summary mode must not
    drop text down to the 512-byte preview only."""
    prompt = "Continue exactly where you left off.\n\n" + ("detail " * 200)
    payload = chatter_payload(prompt, mode="summary")
    assert payload is not None
    assert payload["text"] == prompt
    assert payload["length"] == len(prompt)
    assert len(payload["preview"]) <= 512


def test_summarize_tool_off_mode() -> None:
    assert summarize_tool("Bash", "echo hi", mode="off") is None


def test_summarize_tool_string_raw() -> None:
    result = summarize_tool("Read", "/path/to/file.py", mode="summary")
    assert result is not None
    assert result["name"] == "Read"
    assert "/path/to/file.py" in result["text"]


def test_summarize_tool_dict_raw() -> None:
    result = summarize_tool("Edit", {"file": "a.py", "old": "x", "new": "y"}, mode="full")
    assert result is not None
    assert result["name"] == "Edit"
    assert "a.py" in result["text"]


def test_summarize_tool_non_serializable() -> None:
    class Weird:
        pass

    result = summarize_tool("Custom", Weird(), mode="summary")
    assert result is not None
    assert result["name"] == "Custom"


def test_summarize_tool_raises_type_error_falls_back_to_repr() -> None:
    """json.dumps(default=str) still raises TypeError for a dict with a
    non-str-coercible key (e.g. a tuple) -- summarize_tool must fall back to
    repr() rather than propagate."""
    raw = {(1, 2): "value"}
    result = summarize_tool("Odd", raw, mode="summary")
    assert result is not None
    assert result["name"] == "Odd"
    assert repr(raw) in result["text"]


def test_dump_transcript(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "events.jsonl"
    path.write_text(
        '{"event_type":"chatter.delta","payload":{"text":"Hi"}}\n'
        '{"event_type":"chatter.assistant","payload":{"text":" there"}}\n',
        encoding="utf-8",
    )
    dump_transcript(path)
    out = capsys.readouterr().out
    assert "Hi" in out
    assert "there" in out
