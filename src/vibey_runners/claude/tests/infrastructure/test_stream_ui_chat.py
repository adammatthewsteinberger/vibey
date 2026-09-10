# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Stream UI chat panel: continuous log, full prompts, no per-turn wipe."""

from __future__ import annotations

import io
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from claudeloop.infrastructure.stream_ui import (
    BufferingStreamUi,
    NullStreamUi,
    StreamUiState,
    dump_transcript,
    follow_events_plain,
    iter_event_records,
    run_textual_app,
)
from claudeloop.infrastructure.stream_ui.app import (
    ChatUpdate,
    _payload_text,
    chat_update_for_record,
)


def test_buffering_stream_ui_queues_full_prompts_without_wiping_history() -> None:
    ui = BufferingStreamUi()
    ui.on_prompt("first prompt " + ("x" * 600))
    ui.on_delta("hello", turn_id="t1", seq=1)
    ui.on_turn_boundary(turn_id="t2", attempt=2)
    ui.on_prompt("second prompt")
    ui.on_assistant("done")
    assert len(ui.prompts) == 2
    assert ui.prompts[0].startswith("first prompt ")
    assert len(ui.prompts[0]) > 512
    assert ui.prompts[1] == "second prompt"
    assert ui.assistants == ["done"]
    # Continuous chat: turn boundary must not erase streamed assistant text.
    assert "hello" in ui.state.assistant


def test_chat_update_appends_prompt_without_clearing() -> None:
    update = chat_update_for_record(
        {
            "event_type": "chatter.prompt",
            "payload": {"text": "full prompt body", "preview": "full"},
        }
    )
    assert update.clear is False
    assert "full prompt body" in "".join(update.assistant_lines)
    assert "prompt" in "".join(update.assistant_lines).lower()


def test_chat_update_skips_assistant_when_deltas_already_streamed() -> None:
    first = chat_update_for_record(
        {"event_type": "chatter.delta", "payload": {"text": "partial"}},
        saw_delta=False,
    )
    assert first.saw_delta is True
    assert first.assistant_lines == ["partial"]
    second = chat_update_for_record(
        {"event_type": "chatter.assistant", "payload": {"text": "partial full"}},
        saw_delta=True,
    )
    assert second.assistant_lines == []


def test_chat_update_prefers_full_text_over_preview() -> None:
    update = chat_update_for_record(
        {
            "event_type": "chatter.prompt",
            "payload": {"text": "COMPLETE_PROMPT_BODY", "preview": "COMP"},
        }
    )
    joined = "".join(update.assistant_lines)
    assert "COMPLETE_PROMPT_BODY" in joined
    assert joined.count("COMP") == 0 or "COMPLETE_PROMPT_BODY" in joined


class TestPayloadText:
    def test_prefers_text(self) -> None:
        assert _payload_text({"text": "hello", "preview": "hi"}) == "hello"

    def test_falls_back_to_preview(self) -> None:
        assert _payload_text({"preview": "hi"}) == "hi"

    def test_empty_text_falls_back(self) -> None:
        assert _payload_text({"text": "", "preview": "hi"}) == "hi"

    def test_none_text_falls_back(self) -> None:
        assert _payload_text({"text": None, "preview": "hi"}) == "hi"

    def test_no_text_no_preview(self) -> None:
        assert _payload_text({}) == ""


class TestChatUpdateDefaults:
    def test_defaults(self) -> None:
        u = ChatUpdate()
        assert u.clear is False
        assert u.assistant_lines == []
        assert u.tool_lines == []
        assert u.saw_delta is False
        assert u.header_dirty is False


class TestChatUpdateForTool:
    def test_tool_event(self) -> None:
        update = chat_update_for_record(
            {"event_type": "chatter.tool", "payload": {"name": "Bash", "text": "echo hi"}},
        )
        assert len(update.tool_lines) == 1
        assert "Bash" in update.tool_lines[0]

    def test_tool_with_preview_fallback(self) -> None:
        update = chat_update_for_record(
            {"event_type": "chatter.tool", "payload": {"name": "Read", "preview": "/a.py"}},
        )
        assert "Read" in update.tool_lines[0]
        assert "/a.py" in update.tool_lines[0]


class TestChatUpdateAssistantNoNewline:
    def test_assistant_adds_newline_if_missing(self) -> None:
        update = chat_update_for_record(
            {"event_type": "chatter.assistant", "payload": {"text": "hello"}},
            saw_delta=False,
        )
        assert update.assistant_lines[-1] == "\n"

    def test_assistant_no_extra_newline(self) -> None:
        update = chat_update_for_record(
            {"event_type": "chatter.assistant", "payload": {"text": "hello\n"}},
            saw_delta=False,
        )
        assert update.assistant_lines == ["hello\n"]


class TestChatUpdateClearOnPrompt:
    def test_clear_on_prompt(self) -> None:
        update = chat_update_for_record(
            {"event_type": "chatter.prompt", "payload": {"text": "go"}},
            clear_on_prompt=True,
        )
        assert update.clear is True

    def test_no_clear_default(self) -> None:
        update = chat_update_for_record(
            {"event_type": "chatter.prompt", "payload": {"text": "go"}},
        )
        assert update.clear is False


class TestChatUpdateUnknownEvent:
    def test_unknown_event_returns_empty_update(self) -> None:
        update = chat_update_for_record(
            {"event_type": "some.unknown.event", "payload": {}},
        )
        assert update.assistant_lines == []
        assert update.tool_lines == []


class TestChatUpdateBadPayload:
    def test_non_dict_payload(self) -> None:
        update = chat_update_for_record(
            {"event_type": "chatter.delta", "payload": "not a dict"},
        )
        assert update.assistant_lines == []


class TestNullStreamUi:
    def test_all_methods_are_noops(self) -> None:
        ui = NullStreamUi()
        ui.on_delta("x", turn_id="t", seq=1)
        ui.on_turn_boundary(turn_id="t", attempt=1)
        ui.on_prompt("hi")
        ui.on_assistant("bye")
        ui.on_tool("Bash", "echo")
        ui.on_status({"model": "x"})
        assert ui.close() is None


class TestBufferingStreamUiExtended:
    def test_on_tool_caps_at_50(self) -> None:
        ui = BufferingStreamUi()
        for i in range(60):
            ui.on_tool(f"t{i}", "summary")
        assert len(ui.state.tools) == 50

    def test_on_status_updates_fields(self) -> None:
        ui = BufferingStreamUi()
        ui.on_status(
            {
                "model": "claude-sonnet",
                "effort": "high",
                "phase": "RUNNING",
                "dollars_spent": 1.23,
                "run_id": "r1",
                "trace_id": "tr1",
            }
        )
        assert ui.state.model == "claude-sonnet"
        assert ui.state.effort == "high"
        assert ui.state.phase == "RUNNING"
        assert ui.state.spend == 1.23
        assert ui.state.run_id == "r1"
        assert ui.state.trace_id == "tr1"

    def test_close(self) -> None:
        ui = BufferingStreamUi()
        assert ui.closed is False
        ui.close()
        assert ui.closed is True

    def test_on_assistant_skips_when_delta_seen(self) -> None:
        ui = BufferingStreamUi()
        ui.on_delta("partial", turn_id="t1", seq=1)
        ui.on_assistant("full text")
        assert ui.assistants == []

    def test_on_assistant_appends_when_no_delta(self) -> None:
        ui = BufferingStreamUi()
        ui.on_assistant("response")
        assert ui.assistants == ["response"]
        assert "response" in ui.state.assistant


class TestStreamUiState:
    def test_defaults(self) -> None:
        s = StreamUiState()
        assert s.run_id == ""
        assert s.attempt == 0
        assert s.spend == 0.0


class TestIterEventRecords:
    def test_reads_jsonl(self, tmp_path: Path) -> None:
        f = tmp_path / "events.jsonl"
        f.write_text(
            '{"event_type":"chatter.delta","payload":{"text":"hi"}}\n'
            '{"event_type":"chatter.prompt","payload":{"text":"go"}}\n',
            encoding="utf-8",
        )
        records = list(iter_event_records(f))
        assert len(records) == 2
        assert records[0]["event_type"] == "chatter.delta"

    def test_skips_bad_json(self, tmp_path: Path) -> None:
        f = tmp_path / "events.jsonl"
        f.write_text('{"good":1}\n{bad\n{"also":2}\n', encoding="utf-8")
        records = list(iter_event_records(f))
        assert len(records) == 2

    def test_skips_empty_lines(self, tmp_path: Path) -> None:
        f = tmp_path / "events.jsonl"
        f.write_text('\n{"a":1}\n\n{"b":2}\n\n', encoding="utf-8")
        records = list(iter_event_records(f))
        assert len(records) == 2

    def test_missing_file(self, tmp_path: Path) -> None:
        records = list(iter_event_records(tmp_path / "nope.jsonl"))
        assert records == []


class TestDumpTranscript:
    def test_dumps_to_file(self, tmp_path: Path) -> None:
        f = tmp_path / "events.jsonl"
        f.write_text(
            '{"event_type":"chatter.prompt","payload":{"text":"hello"}}\n'
            '{"event_type":"chatter.delta","payload":{"text":"world"}}\n'
            '{"event_type":"chatter.assistant","payload":{"text":"done"}}\n',
            encoding="utf-8",
        )
        buf = io.StringIO()
        dump_transcript(f, file=buf)
        output = buf.getvalue()
        assert "hello" in output
        assert "world" in output
        assert "done" in output


class TestFollowEventsPlain:
    def test_one_pass_no_follow(self, tmp_path: Path) -> None:
        f = tmp_path / "events.jsonl"
        f.write_text(
            '{"event_type":"chatter.delta","payload":{"text":"hi"}}\n'
            '{"event_type":"chatter.prompt","payload":{"text":"go"}}\n'
            '{"event_type":"chatter.assistant","payload":{"text":"done"}}\n',
            encoding="utf-8",
        )
        buf = io.StringIO()
        with patch.object(sys, "stdout", buf):
            follow_events_plain(f, follow=False)
        output = buf.getvalue()
        assert "hi" in output
        assert "[chatter.prompt] go" in output
        assert "[chatter.assistant] done" in output

    def test_skips_bad_json_lines(self, tmp_path: Path) -> None:
        f = tmp_path / "events.jsonl"
        f.write_text(
            '{"event_type":"chatter.delta","payload":{"text":"ok"}}\n'
            "{bad json}\n"
            '{"event_type":"chatter.delta","payload":{"text":"fine"}}\n',
            encoding="utf-8",
        )
        buf = io.StringIO()
        with patch.object(sys, "stdout", buf):
            follow_events_plain(f, follow=False)
        output = buf.getvalue()
        assert "ok" in output
        assert "fine" in output

    def test_missing_file_no_follow(self, tmp_path: Path) -> None:
        buf = io.StringIO()
        with patch.object(sys, "stdout", buf):
            follow_events_plain(tmp_path / "nope.jsonl", follow=False)
        assert buf.getvalue() == ""

    def test_delta_uses_preview_fallback(self, tmp_path: Path) -> None:
        f = tmp_path / "events.jsonl"
        f.write_text(
            '{"event_type":"chatter.tool","payload":{"preview":"listing","text":""}}\n',
            encoding="utf-8",
        )
        buf = io.StringIO()
        with patch.object(sys, "stdout", buf):
            follow_events_plain(f, follow=False)
        output = buf.getvalue()
        assert "[chatter.tool]" in output


class TestRunTextualApp:
    def test_raises_when_not_tty(self, tmp_path: Path) -> None:
        with (
            patch.object(sys.stdout, "isatty", return_value=False),
            pytest.raises(RuntimeError, match="stream UI requires a TTY"),
        ):
            run_textual_app(events_path=tmp_path / "events.jsonl")

    def test_launches_stream_app_when_tty(self, tmp_path: Path) -> None:
        """When stdout is a TTY, run_textual_app builds a StreamApp with the
        given options and calls .run() on it -- the deferred import of
        StreamApp happens inside the function, so it's patched at its own
        module path."""
        from unittest.mock import MagicMock

        mock_app_instance = MagicMock()
        mock_app_cls = MagicMock(return_value=mock_app_instance)

        with (
            patch.object(sys.stdout, "isatty", return_value=True),
            patch("claudeloop.infrastructure.stream_ui.app.StreamApp", mock_app_cls),
        ):
            run_textual_app(
                events_path=tmp_path / "events.jsonl",
                follow=False,
                replay=True,
                speed=2.0,
            )

        mock_app_cls.assert_called_once()
        _, kwargs = mock_app_cls.call_args
        assert kwargs["events_path"] == tmp_path / "events.jsonl"
        assert kwargs["follow"] is False
        assert kwargs["replay"] is True
        assert kwargs["speed"] == 2.0
        mock_app_instance.run.assert_called_once_with()


class TestBufferingStreamUiPartialBranches:
    def test_on_assistant_empty_text(self) -> None:
        """on_assistant with empty text when no delta seen (branch 79->exit)."""
        ui = BufferingStreamUi()
        ui.on_assistant("")
        assert ui.assistants == []
        assert ui.state.assistant == ""

    def test_on_status_empty_dict(self) -> None:
        """on_status({}) skips all key branches (88->90..98->exit)."""
        ui = BufferingStreamUi()
        old_model = ui.state.model
        ui.on_status({})
        assert ui.state.model == old_model


class TestDumpTranscriptPartialBranches:
    def test_non_chatter_event_type(self, tmp_path: Path) -> None:
        """Event types not matching delta/prompt/assistant loop back (129->122)."""
        f = tmp_path / "events.jsonl"
        f.write_text(
            '{"event_type":"turn.starting","payload":{}}\n'
            '{"event_type":"chatter.delta","payload":{"text":"ok"}}\n',
            encoding="utf-8",
        )
        buf = io.StringIO()
        dump_transcript(f, file=buf)
        output = buf.getvalue()
        assert "ok" in output
        assert "turn.starting" not in output


class TestFollowEventsPlainPartialBranches:
    def test_existing_file_no_new_data(self, tmp_path: Path) -> None:
        """File exists but all data already read → chunk is empty (172->188)."""
        f = tmp_path / "events.jsonl"
        f.write_text(
            '{"event_type":"chatter.delta","payload":{"text":"hi"}}\n',
            encoding="utf-8",
        )
        buf = io.StringIO()
        with patch.object(sys, "stdout", buf):
            follow_events_plain(f, follow=False)
        buf2 = io.StringIO()
        with patch.object(sys, "stdout", buf2):
            follow_events_plain(f, follow=False)
        assert "hi" in buf.getvalue()

    def test_non_chatter_event_in_follow(self, tmp_path: Path) -> None:
        """Event type not starting with 'chatter.' loops back (183->173)."""
        f = tmp_path / "events.jsonl"
        f.write_text(
            '{"event_type":"model.profile_changed","payload":{"model":"opus"}}\n'
            '{"event_type":"chatter.delta","payload":{"text":"ok"}}\n',
            encoding="utf-8",
        )
        buf = io.StringIO()
        with patch.object(sys, "stdout", buf):
            follow_events_plain(f, follow=False)
        output = buf.getvalue()
        assert "ok" in output
        assert "model.profile_changed" not in output


class TestFollowEventsPlainChunkEmpty:
    def test_file_exists_but_chunk_empty_on_second_pass(self, tmp_path: Path) -> None:
        """File exists, first pass reads all data, second pass chunk is empty
        (172->188). follow=True lets the while loop iterate twice; raise on
        the second sleep so the empty-chunk path is reached."""
        f = tmp_path / "events.jsonl"
        f.write_text(
            '{"event_type":"chatter.delta","payload":{"text":"hi"}}\n',
            encoding="utf-8",
        )
        calls: list[float] = []

        class _StopLoop(Exception):
            pass

        def fake_sleep(seconds: float) -> None:
            calls.append(seconds)
            if len(calls) >= 2:
                raise _StopLoop

        buf = io.StringIO()
        with (
            patch.object(sys, "stdout", buf),
            patch("claudeloop.infrastructure.stream_ui.time.sleep", side_effect=fake_sleep),
            pytest.raises(_StopLoop),
        ):
            follow_events_plain(f, follow=True, poll_seconds=0.1)
        assert "hi" in buf.getvalue()
        assert len(calls) == 2


class TestFollowEventsPlainSleeps:
    def test_sleeps_between_polls_when_following(self, tmp_path: Path) -> None:
        """follow=True must actually sleep between polls rather than
        busy-looping -- verified by breaking out of the infinite loop via the
        mocked time.sleep's side effect."""

        class _StopLoop(Exception):
            pass

        calls: list[float] = []

        def fake_sleep(seconds: float) -> None:
            calls.append(seconds)
            raise _StopLoop

        with (
            patch("claudeloop.infrastructure.stream_ui.time.sleep", side_effect=fake_sleep),
            pytest.raises(_StopLoop),
        ):
            follow_events_plain(tmp_path / "nope.jsonl", follow=True, poll_seconds=0.05)

        assert calls == [0.05]
