# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agyloop.infrastructure.stream_ui import (
    NullStreamUi,
    StreamApp,
    StreamUiState,
    dump_transcript,
    follow_events_plain,
    iter_event_records,
    run_textual_app,
)


def test_null_stream_ui() -> None:
    ui = NullStreamUi()
    ui.on_delta("delta", turn_id="t1", seq=1)
    ui.on_turn_boundary(turn_id="t1", attempt=1)
    ui.on_prompt("prompt")
    ui.on_assistant("assistant")
    ui.on_tool("tool", "summary")
    ui.on_status({"status": "running"})
    assert ui.close() is None


def test_stream_ui_state() -> None:
    state = StreamUiState(run_id="r1", attempt=1, phase="RUNNING", assistant="hi", tools=["t1"])
    assert state.run_id == "r1"
    assert state.tools == ["t1"]


def test_iter_event_records(tmp_path: Path) -> None:
    missing = tmp_path / "missing.jsonl"
    assert list(iter_event_records(missing)) == []

    events_file = tmp_path / "events.jsonl"
    events_file.write_text(
        "\n"
        '{"event_type": "chatter.delta", "payload": {"text": "hello "}}\n'
        "not json\n"
        '{"event_type": "chatter.delta", "payload": {"text": "world"}}\n'
        "\n",
        encoding="utf-8",
    )
    records = list(iter_event_records(events_file))
    assert len(records) == 2
    assert records[0]["event_type"] == "chatter.delta"


def test_dump_transcript(tmp_path: Path) -> None:
    events_file = tmp_path / "events.jsonl"
    events_file.write_text(
        json.dumps({"event_type": "chatter.prompt", "payload": {"text": "What is 2+2?"}})
        + "\n"
        + json.dumps({"event_type": "chatter.delta", "payload": {"text": "4"}})
        + "\n"
        + json.dumps({"event_type": "chatter.assistant", "payload": {"preview": "It is 4."}})
        + "\n"
        + json.dumps({"event_type": "other", "payload": "not a dict"})
        + "\n",
        encoding="utf-8",
    )
    buf = io.StringIO()
    dump_transcript(events_file, file=buf)
    out = buf.getvalue()
    assert "--- prompt ---" in out
    assert "What is 2+2?" in out
    assert "4" in out
    assert "--- assistant ---" in out
    assert "It is 4." in out


def test_follow_events_plain(tmp_path: Path) -> None:
    events_file = tmp_path / "events.jsonl"
    events_file.write_text(
        json.dumps({"event_type": "chatter.delta", "payload": {"text": "chunk"}})
        + "\n"
        + "bad json\n"
        + json.dumps(
            {"event_type": "chatter.tool", "payload": {"name": "read", "preview": "file.py"}}
        )
        + "\n"
        + json.dumps({"event_type": "chatter.other", "payload": "not dict"})
        + "\n",
        encoding="utf-8",
    )
    with patch("sys.stdout.write") as mock_write, patch("sys.stdout.flush"):
        follow_events_plain(events_file, follow=False)
        assert mock_write.called

        # Loop with follow=True and mock sleep
        def _break_sleep(_s: float) -> None:
            raise StopIteration

        with patch("time.sleep", side_effect=_break_sleep), pytest.raises(StopIteration):
            follow_events_plain(events_file, follow=True)


def test_stream_app_drain(tmp_path: Path) -> None:
    events_file = tmp_path / "events.jsonl"
    events_file.write_text(
        json.dumps({"event_type": "chatter.prompt", "payload": {"text": "prompt text"}})
        + "\n"
        + json.dumps({"event_type": "chatter.delta", "payload": {"text": "delta text"}})
        + "\n"
        + json.dumps({"event_type": "chatter.assistant", "payload": {"text": "assistant text"}})
        + "\n"
        + json.dumps(
            {"event_type": "chatter.tool", "payload": {"name": "grep", "summary": "query"}}
        )
        + "\n"
        + json.dumps({"event_type": "chatter.tool", "payload": {}})
        + "\n"
        + json.dumps({"event_type": "custom.event", "payload": {}})
        + "\n"
        + json.dumps({"event_type": "chatter.other", "payload": "not a dict"})
        + "\n"
        + json.dumps({"event_type": "chatter.assistant", "payload": {"text": ""}})
        + "\n"
        + "invalid json\n",
        encoding="utf-8",
    )
    app = StreamApp(events_path=events_file, follow=False, replay=True, speed=1.0)
    mock_log = MagicMock()
    with patch.object(app, "query_one", return_value=mock_log):
        app._drain(follow=False)
        assert mock_log.write.called

        # Test assistant write when delta was not seen
        events_file.write_text(
            json.dumps({"event_type": "chatter.prompt", "payload": {"text": "p"}})
            + "\n"
            + json.dumps({"event_type": "chatter.assistant", "payload": {"text": "a"}})
            + "\n",
            encoding="utf-8",
        )
        app._offset = 0
        app._drain(follow=False)
        assert mock_log.write.called

    # When file does not exist
    missing_app = StreamApp(events_path=tmp_path / "missing", follow=False)
    with patch.object(missing_app, "query_one", return_value=mock_log):
        missing_app._drain(follow=False)

    # Compose and on_mount and tick
    widgets = list(app.compose())
    assert len(widgets) == 3
    with patch.object(app, "set_interval") as mock_interval, patch.object(app, "_drain"):
        app.on_mount()
        assert mock_interval.called
        app._tick()


def test_run_textual_app(tmp_path: Path) -> None:
    events_file = tmp_path / "events.jsonl"
    events_file.write_text(
        '{"event_type": "chatter.delta", "payload": {"text": "hi"}}\n', encoding="utf-8"
    )

    with patch("sys.stdout.isatty", return_value=False):
        # Non-tty + replay -> dump_transcript
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            run_textual_app(events_path=events_file, replay=True)
            assert "hi" in buf.getvalue()

        # Non-tty + no replay -> RuntimeError
        with pytest.raises(RuntimeError, match="stream UI requires a TTY"):
            run_textual_app(events_path=events_file, replay=False)

    # TTY -> StreamApp.run
    with (
        patch("sys.stdout.isatty", return_value=True),
        patch("agyloop.infrastructure.stream_ui.StreamApp.run") as mock_run,
    ):
        run_textual_app(events_path=events_file, follow=True, replay=False)
        assert mock_run.called
