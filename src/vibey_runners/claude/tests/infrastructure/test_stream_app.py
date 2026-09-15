# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Tests for infrastructure/stream_ui/app.py — StreamApp Textual TUI."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from textual.css.query import NoMatches

from claudeloop.infrastructure.stream_ui import BufferingStreamUi, StreamUiState
from claudeloop.infrastructure.stream_ui.app import ChatUpdate, StreamApp, chat_update_for_record


def _write_events(path: Path, events: list[dict]) -> Path:
    f = path / "events.jsonl"
    f.write_text(
        "\n".join(json.dumps(e) for e in events) + "\n",
        encoding="utf-8",
    )
    return f


def _make_app(
    events_path: Path, *, replay: bool = False, follow: bool = True, **kwargs
) -> StreamApp:
    return StreamApp(
        events_path=events_path,
        replay=replay,
        follow=follow,
        **kwargs,
    )


class TestStreamAppInit:
    def test_defaults(self, tmp_path: Path) -> None:
        app = _make_app(tmp_path / "events.jsonl")
        assert app.follow is True
        assert app.replay is False
        assert app.speed == 1.0
        assert isinstance(app.state, StreamUiState)
        assert app._offset == 0
        assert app._records == []
        assert app._saw_delta is False

    def test_with_initial_state(self, tmp_path: Path) -> None:
        state = StreamUiState(run_id="r1", model="opus")
        app = _make_app(tmp_path / "events.jsonl", initial=state)
        assert app.state.run_id == "r1"
        assert app.state.model == "opus"

    def test_with_live_source(self, tmp_path: Path) -> None:
        live = BufferingStreamUi()
        app = _make_app(tmp_path / "events.jsonl", live_source=live)
        assert app.live_source is live


class TestStreamAppHeaderText:
    def test_header_text(self, tmp_path: Path) -> None:
        state = StreamUiState(
            run_id="r1",
            trace_id="t1",
            model="opus",
            effort="high",
            attempt=3,
            phase="RUNNING",
        )
        state.spend = 1.5
        app = _make_app(tmp_path / "events.jsonl", initial=state)
        text = app._header_text()
        assert "r1" in text
        assert "t1" in text
        assert "opus" in text
        assert "high" in text
        assert "3" in text
        assert "RUNNING" in text
        assert "1.5" in text


class TestStreamAppLoadAll:
    def test_load_all_with_prompts(self, tmp_path: Path) -> None:
        events = [
            {"event_type": "chatter.prompt", "payload": {"text": "first"}},
            {"event_type": "chatter.delta", "payload": {"text": "hi"}},
            {"event_type": "chatter.prompt", "payload": {"text": "second"}},
            {"event_type": "chatter.delta", "payload": {"text": "bye"}},
        ]
        f = _write_events(tmp_path, events)
        app = _make_app(f, replay=True)
        app._load_all()
        assert len(app._records) == 4
        assert app._turn_starts == [0, 2]

    def test_load_all_no_prompts(self, tmp_path: Path) -> None:
        events = [
            {"event_type": "chatter.delta", "payload": {"text": "hi"}},
        ]
        f = _write_events(tmp_path, events)
        app = _make_app(f, replay=True)
        app._load_all()
        assert len(app._records) == 1
        assert app._turn_starts == [0]

    def test_load_all_missing_file(self, tmp_path: Path) -> None:
        app = _make_app(tmp_path / "nope.jsonl", replay=True)
        app._load_all()
        assert app._records == []

    def test_load_all_skips_bad_json(self, tmp_path: Path) -> None:
        f = tmp_path / "events.jsonl"
        f.write_text(
            '{"event_type":"chatter.delta","payload":{"text":"ok"}}\n'
            "{bad}\n"
            "\n"
            '{"event_type":"chatter.delta","payload":{"text":"fine"}}\n',
            encoding="utf-8",
        )
        app = _make_app(f, replay=True)
        app._load_all()
        assert len(app._records) == 2


class TestStreamAppCompose:
    @pytest.mark.asyncio
    async def test_compose_widgets(self, tmp_path: Path) -> None:
        f = _write_events(tmp_path, [])
        app = _make_app(f, follow=False)
        async with app.run_test(size=(120, 40)):
            assert app.query_one("#assistant") is not None
            assert app.query_one("#tools") is not None
            assert app.query_one("#header-bar") is not None
            assert app.query_one("#thinking-bar") is not None


class TestStreamAppApplyRecord:
    @pytest.mark.asyncio
    async def test_apply_record_sets_trace_and_run(self, tmp_path: Path) -> None:
        events = [
            {
                "event_type": "chatter.delta",
                "payload": {"text": "hi"},
                "trace_id": "t1",
                "run_id": "r1",
            },
        ]
        f = _write_events(tmp_path, events)
        app = _make_app(f, follow=False)
        async with app.run_test(size=(120, 40)):
            app._apply_record(events[0])
            assert app.state.trace_id == "t1"
            assert app.state.run_id == "r1"

    @pytest.mark.asyncio
    async def test_apply_record_model_profile_changed(self, tmp_path: Path) -> None:
        events = [
            {"event_type": "model.profile_changed", "payload": {"model": "opus", "effort": "max"}},
        ]
        f = _write_events(tmp_path, events)
        app = _make_app(f, follow=False)
        async with app.run_test(size=(120, 40)):
            app._apply_record(events[0])
            assert app.state.model == "opus"
            assert app.state.effort == "max"

    @pytest.mark.asyncio
    async def test_apply_record_turn_starting(self, tmp_path: Path) -> None:
        events = [
            {"event_type": "turn.starting", "attempt": 5},
        ]
        f = _write_events(tmp_path, events)
        app = _make_app(f, follow=False)
        async with app.run_test(size=(120, 40)):
            app._apply_record(events[0])
            assert app.state.attempt == 5


class TestStreamAppTickFollow:
    @pytest.mark.asyncio
    async def test_tick_follow_reads_events(self, tmp_path: Path) -> None:
        events = [
            {"event_type": "chatter.delta", "payload": {"text": "hello"}},
        ]
        f = _write_events(tmp_path, events)
        app = _make_app(f, follow=True)
        async with app.run_test(size=(120, 40)):
            app._tick_follow()
            assert app._offset > 0
            assert app._saw_delta is True

    @pytest.mark.asyncio
    async def test_tick_follow_paused_skips(self, tmp_path: Path) -> None:
        events = [
            {"event_type": "chatter.delta", "payload": {"text": "hi"}},
        ]
        f = _write_events(tmp_path, events)
        app = _make_app(f, follow=True)
        # Pause before mount so the real interval scheduled by on_mount cannot
        # consume the file while run_test is still starting the application.
        app.paused = True
        async with app.run_test(size=(120, 40)):
            app._tick_follow()
            assert app._offset == 0

    @pytest.mark.asyncio
    async def test_tick_follow_missing_file(self, tmp_path: Path) -> None:
        app = _make_app(tmp_path / "nope.jsonl", follow=True)
        async with app.run_test(size=(120, 40)):
            app._tick_follow()
            assert app._offset == 0

    @pytest.mark.asyncio
    async def test_tick_follow_with_live_source_skips_chatter(self, tmp_path: Path) -> None:
        events = [
            {"event_type": "chatter.delta", "payload": {"text": "hi"}},
            {"event_type": "chatter.tool", "payload": {"name": "Bash", "text": "echo"}},
            {"event_type": "model.profile_changed", "payload": {"model": "opus"}},
        ]
        f = _write_events(tmp_path, events)
        live = BufferingStreamUi()
        app = _make_app(f, follow=True, live_source=live)
        async with app.run_test(size=(120, 40)):
            app._tick_follow()
            assert app.state.model == "opus"

    @pytest.mark.asyncio
    async def test_tick_follow_skips_bad_json_lines(self, tmp_path: Path) -> None:
        f = tmp_path / "events.jsonl"
        f.write_text(
            '{"event_type":"chatter.delta","payload":{"text":"ok"}}\n'
            "{not valid json}\n"
            '{"event_type":"chatter.delta","payload":{"text":"fine"}}\n',
            encoding="utf-8",
        )
        app = _make_app(f, follow=True)
        async with app.run_test(size=(120, 40)):
            app._tick_follow()
            # Both valid lines applied; the malformed middle line was
            # skipped via the JSONDecodeError `continue`, not raised.
            assert app._offset > 0
            assert app._saw_delta is True


class TestStreamAppTickLive:
    def test_tick_live_before_mount_is_inert(self, tmp_path: Path) -> None:
        """A timer racing with teardown must not query removed widgets."""
        f = _write_events(tmp_path, [])
        live = BufferingStreamUi()
        live.on_assistant("final answer")
        app = _make_app(f, follow=True, live_source=live)

        app._tick_live()

        assert live.assistants == ["final answer"]

    def test_tick_live_mount_started_before_screen_is_inert(self, tmp_path: Path) -> None:
        """A mount timer must wait until Textual creates the screen stack."""
        f = _write_events(tmp_path, [])
        live = BufferingStreamUi()
        live.on_assistant("final answer")
        app = _make_app(f, follow=True, live_source=live)
        app._ui_mounted = True

        app._tick_live()

        assert live.assistants == ["final answer"]

    def test_tick_live_mount_started_before_children_is_inert(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A mount timer must wait until every live-tick widget is attached."""
        f = _write_events(tmp_path, [])
        live = BufferingStreamUi()
        live.on_assistant("final answer")
        app = _make_app(f, follow=True, live_source=live)
        app._ui_mounted = True

        def missing_widget(*_args: object, **_kwargs: object) -> None:
            raise NoMatches("#header-bar")

        monkeypatch.setattr(app, "query_one", missing_widget)

        app._tick_live()

        assert live.assistants == ["final answer"]

    @pytest.mark.asyncio
    async def test_tick_live_processes_prompts_deltas_assistants(self, tmp_path: Path) -> None:
        f = _write_events(tmp_path, [])
        live = BufferingStreamUi()
        app = _make_app(f, follow=True, live_source=live)
        async with app.run_test(size=(120, 40)):
            live.on_prompt("hello")
            live.on_delta("world", turn_id="t1", seq=1)
            live.on_assistant("done")
            app._tick_live()
            assert live.prompts == []
            assert live.deltas == []
            assert live.assistants == []

    @pytest.mark.asyncio
    async def test_tick_live_paused_skips(self, tmp_path: Path) -> None:
        f = _write_events(tmp_path, [])
        live = BufferingStreamUi()
        app = _make_app(f, follow=True, live_source=live)
        async with app.run_test(size=(120, 40)):
            live.on_prompt("hello")
            app.paused = True
            app._tick_live()
            assert len(live.prompts) == 1

    @pytest.mark.asyncio
    async def test_tick_live_no_source_returns(self, tmp_path: Path) -> None:
        f = _write_events(tmp_path, [])
        app = _make_app(f, follow=True)
        async with app.run_test(size=(120, 40)):
            app._tick_live()

    @pytest.mark.asyncio
    async def test_tick_live_drains_assistants_without_prior_delta(self, tmp_path: Path) -> None:
        """BufferingStreamUi.on_assistant() only appends to .assistants when
        no delta streamed yet this turn -- so to actually exercise the
        assistants-draining loop in _tick_live, call on_assistant() with no
        preceding on_delta()."""
        f = _write_events(tmp_path, [])
        live = BufferingStreamUi()
        app = _make_app(f, follow=True, live_source=live)
        async with app.run_test(size=(120, 40)):
            live.on_assistant("final answer")
            assert live.assistants == ["final answer"]
            app._tick_live()
            assert live.assistants == []


class TestStreamAppTickReplay:
    def test_tick_replay_before_dom_consumes_nothing(self, tmp_path: Path) -> None:
        events = [{"event_type": "chatter.delta", "payload": {"text": "hi"}}]
        f = _write_events(tmp_path, events)
        app = _make_app(f, replay=True, follow=False)
        app._load_all()
        # No run_test: the DOM does not exist, exactly like an interval
        # dispatched before compose finished. The readiness probe must swallow
        # it and consume nothing, so the next tick replays the record instead.
        app._tick_replay()
        assert app._replay_index == 0

    @pytest.mark.asyncio
    async def test_tick_replay_advances(self, tmp_path: Path) -> None:
        events = [
            {"event_type": "chatter.prompt", "payload": {"text": "go"}},
            {"event_type": "chatter.delta", "payload": {"text": "hi"}},
        ]
        f = _write_events(tmp_path, events)
        app = _make_app(f, replay=True, follow=False)
        # Prevent auto-play timer from racing the manual tick below.
        app._playing = False
        async with app.run_test(size=(120, 40)) as pilot:
            # Wait for compose/mount to finish before driving: entering run_test
            # does not guarantee #assistant is mounted yet, and a single
            # pause() proved insufficient on slow CI runners. Poll the DOM
            # itself — deterministic, since mount always completes.
            while not app.query("#assistant"):
                await pilot.pause()
            app._load_all()
            app._playing = True
            app._tick_replay()
            assert app._replay_index == 1

    @pytest.mark.asyncio
    async def test_tick_replay_paused_skips(self, tmp_path: Path) -> None:
        events = [
            {"event_type": "chatter.delta", "payload": {"text": "hi"}},
        ]
        f = _write_events(tmp_path, events)
        app = _make_app(f, replay=True, follow=False)
        # Set paused before run_test() to prevent auto-play timer race.
        app.paused = True
        async with app.run_test(size=(120, 40)) as pilot:
            # Wait for compose/mount to finish before driving: entering run_test
            # does not guarantee #assistant is mounted yet, and a single
            # pause() proved insufficient on slow CI runners. Poll the DOM
            # itself — deterministic, since mount always completes.
            while not app.query("#assistant"):
                await pilot.pause()
            app._load_all()
            app._tick_replay()
            assert app._replay_index == 0

    @pytest.mark.asyncio
    async def test_tick_replay_not_playing_skips(self, tmp_path: Path) -> None:
        events = [
            {"event_type": "chatter.delta", "payload": {"text": "hi"}},
        ]
        f = _write_events(tmp_path, events)
        app = _make_app(f, replay=True, follow=False)
        # _playing defaults True, and mounting schedules a real 0.05s
        # interval calling _tick_replay -- set it False before run_test()
        # mounts the app, or that timer can race the assertion below under
        # load and advance _replay_index before this test's own manual call.
        app._playing = False
        async with app.run_test(size=(120, 40)) as pilot:
            # Wait for compose/mount to finish before driving: entering run_test
            # does not guarantee #assistant is mounted yet, and a single
            # pause() proved insufficient on slow CI runners. Poll the DOM
            # itself — deterministic, since mount always completes.
            while not app.query("#assistant"):
                await pilot.pause()
            app._load_all()
            app._tick_replay()
            assert app._replay_index == 0

    @pytest.mark.asyncio
    async def test_tick_replay_at_end(self, tmp_path: Path) -> None:
        events = [
            {"event_type": "chatter.delta", "payload": {"text": "hi"}},
        ]
        f = _write_events(tmp_path, events)
        app = _make_app(f, replay=True, follow=False)
        async with app.run_test(size=(120, 40)) as pilot:
            # Wait for compose/mount to finish before driving: entering run_test
            # does not guarantee #assistant is mounted yet, and a single
            # pause() proved insufficient on slow CI runners. Poll the DOM
            # itself — deterministic, since mount always completes.
            while not app.query("#assistant"):
                await pilot.pause()
            app._load_all()
            app._replay_index = 1
            app._tick_replay()
            assert app._replay_index == 1

    @pytest.mark.asyncio
    async def test_tick_replay_speed_zero(self, tmp_path: Path) -> None:
        events = [{"event_type": "chatter.delta", "payload": {"text": f"t{i}"}} for i in range(30)]
        f = _write_events(tmp_path, events)
        app = _make_app(f, replay=True, follow=False, speed=0)
        # _playing defaults True, and mounting schedules a real 0.05s interval
        # calling _tick_replay -- keep it False across mount (see
        # test_tick_replay_not_playing_skips for why), then flip it back to
        # True immediately before the manual call with no `await` in between
        # so the background timer can't sneak in an extra tick first.
        app._playing = False
        async with app.run_test(size=(120, 40)) as pilot:
            # Wait for compose/mount to finish before driving: entering run_test
            # does not guarantee #assistant is mounted yet, and a single
            # pause() proved insufficient on slow CI runners. Poll the DOM
            # itself — deterministic, since mount always completes.
            while not app.query("#assistant"):
                await pilot.pause()
            app._load_all()
            app._playing = True
            app._tick_replay()
            assert app._replay_index == 20

    @pytest.mark.asyncio
    async def test_tick_replay_fast_forward_stops_at_end_of_records(self, tmp_path: Path) -> None:
        """speed<=0 processes up to 20 records per tick; with fewer than 20
        records left, the inner loop must `break` on exhaustion rather than
        index past the end of _records."""
        events = [{"event_type": "chatter.delta", "payload": {"text": f"t{i}"}} for i in range(5)]
        f = _write_events(tmp_path, events)
        app = _make_app(f, replay=True, follow=False, speed=-1)
        app._playing = False
        async with app.run_test(size=(120, 40)) as pilot:
            # Wait for compose/mount to finish before driving: entering run_test
            # does not guarantee #assistant is mounted yet, and a single
            # pause() proved insufficient on slow CI runners. Poll the DOM
            # itself — deterministic, since mount always completes.
            while not app.query("#assistant"):
                await pilot.pause()
            app._load_all()
            app._playing = True
            app._tick_replay()
            assert app._replay_index == 5


class TestStreamAppActions:
    @pytest.mark.asyncio
    async def test_toggle_pause(self, tmp_path: Path) -> None:
        f = _write_events(tmp_path, [])
        app = _make_app(f, follow=True)
        async with app.run_test(size=(120, 40)):
            assert app.paused is False
            app.action_toggle_pause()
            assert app.paused is True
            app.action_toggle_pause()
            assert app.paused is False

    @pytest.mark.asyncio
    async def test_toggle_play_replay_mode(self, tmp_path: Path) -> None:
        f = _write_events(tmp_path, [])
        app = _make_app(f, replay=True, follow=False)
        async with app.run_test(size=(120, 40)):
            assert app._playing is True
            app.action_toggle_play()
            assert app._playing is False
            app.action_toggle_play()
            assert app._playing is True

    @pytest.mark.asyncio
    async def test_toggle_play_follow_mode(self, tmp_path: Path) -> None:
        f = _write_events(tmp_path, [])
        app = _make_app(f, follow=True)
        async with app.run_test(size=(120, 40)):
            app.action_toggle_play()
            assert app.paused is True

    @pytest.mark.asyncio
    async def test_prev_turn_not_replay(self, tmp_path: Path) -> None:
        f = _write_events(tmp_path, [])
        app = _make_app(f, follow=True)
        async with app.run_test(size=(120, 40)):
            app.action_prev_turn()

    @pytest.mark.asyncio
    async def test_next_turn_not_replay(self, tmp_path: Path) -> None:
        f = _write_events(tmp_path, [])
        app = _make_app(f, follow=True)
        async with app.run_test(size=(120, 40)):
            app.action_next_turn()

    @pytest.mark.asyncio
    async def test_prev_turn_replay(self, tmp_path: Path) -> None:
        events = [
            {"event_type": "chatter.prompt", "payload": {"text": "first"}},
            {"event_type": "chatter.delta", "payload": {"text": "a"}},
            {"event_type": "chatter.prompt", "payload": {"text": "second"}},
            {"event_type": "chatter.delta", "payload": {"text": "b"}},
        ]
        f = _write_events(tmp_path, events)
        app = _make_app(f, replay=True, follow=False)
        async with app.run_test(size=(120, 40)) as pilot:
            app._load_all()
            app._replay_index = 3
            app._playing = False  # Pause ticker to prevent race
            await pilot.pause()
            app.action_prev_turn()
            assert app._replay_index == 1

    @pytest.mark.asyncio
    async def test_next_turn_replay(self, tmp_path: Path) -> None:
        events = [
            {"event_type": "chatter.prompt", "payload": {"text": "first"}},
            {"event_type": "chatter.delta", "payload": {"text": "a"}},
            {"event_type": "chatter.prompt", "payload": {"text": "second"}},
            {"event_type": "chatter.delta", "payload": {"text": "b"}},
        ]
        f = _write_events(tmp_path, events)
        app = _make_app(f, replay=True, follow=False)
        async with app.run_test(size=(120, 40)) as pilot:
            app._load_all()
            app._replay_index = 0
            app._playing = False  # Pause ticker to prevent race
            await pilot.pause()
            app.action_next_turn()
            assert app._replay_index == 1

    @pytest.mark.asyncio
    async def test_next_turn_at_last_turn(self, tmp_path: Path) -> None:
        events = [
            {"event_type": "chatter.prompt", "payload": {"text": "only"}},
            {"event_type": "chatter.delta", "payload": {"text": "x"}},
        ]
        f = _write_events(tmp_path, events)
        app = _make_app(f, replay=True, follow=False)
        async with app.run_test(size=(120, 40)):
            app._load_all()
            app._replay_index = 2
            app.action_next_turn()
            assert app._replay_index == 2


class TestStreamAppPartialBranches:
    @pytest.mark.asyncio
    async def test_chat_update_assistant_empty_body(self, tmp_path: Path) -> None:
        """chatter.assistant with empty text+preview → body is empty (74->78)."""
        update = chat_update_for_record(
            {"event_type": "chatter.assistant", "payload": {}},
            saw_delta=False,
        )
        assert update.saw_delta is True
        assert (
            all(line in ("\n", "") for line in update.assistant_lines)
            or update.assistant_lines == []
        )

    @pytest.mark.asyncio
    async def test_append_assistant_empty_text(self, tmp_path: Path) -> None:
        """_append_assistant with empty text is no-op (187->exit)."""
        f = _write_events(tmp_path, [])
        app = _make_app(f, follow=False)
        async with app.run_test(size=(120, 40)):
            app._append_assistant("")

    @pytest.mark.asyncio
    async def test_apply_chat_update_header_not_dirty(self, tmp_path: Path) -> None:
        """ChatUpdate with header_dirty=False skips _refresh_header (207->exit)."""
        f = _write_events(tmp_path, [])
        app = _make_app(f, follow=False)
        async with app.run_test(size=(120, 40)):
            update = ChatUpdate(
                assistant_lines=["text"],
                saw_delta=True,
                header_dirty=False,
            )
            app._apply_chat_update(update)

    @pytest.mark.asyncio
    async def test_apply_record_turn_starting_no_attempt(self, tmp_path: Path) -> None:
        """turn.starting without int attempt skips assignment (242->244)."""
        f = _write_events(tmp_path, [])
        app = _make_app(f, follow=False)
        async with app.run_test(size=(120, 40)):
            app._apply_record({"event_type": "turn.starting"})
            assert app.state.attempt == 0

    @pytest.mark.asyncio
    async def test_tick_live_second_delta_skips_thinking(self, tmp_path: Path) -> None:
        """Second delta in same turn: _saw_delta is True (283->285)."""
        f = _write_events(tmp_path, [])
        live = BufferingStreamUi()
        app = _make_app(f, follow=True, live_source=live)
        async with app.run_test(size=(120, 40)):
            live.on_delta("first", turn_id="t1", seq=1)
            app._tick_live()
            assert app._saw_delta is True
            live.on_delta("second", turn_id="t1", seq=2)
            app._tick_live()
            assert app._saw_delta is True

    @pytest.mark.asyncio
    async def test_prev_turn_all_starts_before_current(self, tmp_path: Path) -> None:
        """All turn_starts < current-1 → for loop exhausts without break (325->330)."""
        events = [
            {"event_type": "chatter.prompt", "payload": {"text": "first"}},
            {"event_type": "chatter.delta", "payload": {"text": "a"}},
            {"event_type": "chatter.prompt", "payload": {"text": "second"}},
            {"event_type": "chatter.delta", "payload": {"text": "b"}},
        ]
        f = _write_events(tmp_path, events)
        app = _make_app(f, replay=True, follow=False)
        # Pause before mount; setting this after run_test yields leaves a race
        # with the 0.05-second replay interval on slower CI runners.
        app._playing = False
        async with app.run_test(size=(120, 40)) as pilot:
            app._load_all()
            app._replay_index = 5
            await pilot.pause()
            app.action_prev_turn()
            assert app._replay_index == 3  # prev(2) + 1 per line 335


class TestStreamAppThinking:
    @pytest.mark.asyncio
    async def test_set_thinking_on_off(self, tmp_path: Path) -> None:
        f = _write_events(tmp_path, [])
        app = _make_app(f, follow=False)
        async with app.run_test(size=(120, 40)):
            app._set_thinking(True)
            assert app._thinking is True
            bar = app.query_one("#thinking-bar")
            # Static has no public `.renderable`; the content set by update()
            # is read back through render().
            assert "thinking" in str(bar.render()).lower()

            app._set_thinking(False)
            assert app._thinking is False

    @pytest.mark.asyncio
    async def test_tick_thinking_cycles(self, tmp_path: Path) -> None:
        f = _write_events(tmp_path, [])
        app = _make_app(f, follow=False)
        async with app.run_test(size=(120, 40)):
            app._set_thinking(True)
            frames = []
            for _ in range(4):
                app._tick_thinking()
                frames.append(app._thinking_frame)
            assert frames == [1, 2, 0, 1]

    @pytest.mark.asyncio
    async def test_tick_thinking_inactive_noop(self, tmp_path: Path) -> None:
        f = _write_events(tmp_path, [])
        app = _make_app(f, follow=False)
        async with app.run_test(size=(120, 40)):
            app._tick_thinking()
            assert app._thinking_frame == 0


class TestStreamAppApplyChatUpdate:
    @pytest.mark.asyncio
    async def test_apply_with_clear(self, tmp_path: Path) -> None:
        f = _write_events(tmp_path, [])
        app = _make_app(f, follow=False)
        async with app.run_test(size=(120, 40)):
            from claudeloop.infrastructure.stream_ui.app import ChatUpdate

            update = ChatUpdate(
                clear=True,
                assistant_lines=["new content"],
                tool_lines=["tool: info"],
                saw_delta=True,
                header_dirty=True,
            )
            app._apply_chat_update(update)
            assert app._saw_delta is True

    @pytest.mark.asyncio
    async def test_apply_prompt_starts_thinking(self, tmp_path: Path) -> None:
        f = _write_events(tmp_path, [])
        app = _make_app(f, follow=False)
        async with app.run_test(size=(120, 40)):
            from claudeloop.infrastructure.stream_ui.app import ChatUpdate

            update = ChatUpdate(
                assistant_lines=["prompt text"],
                saw_delta=False,
                header_dirty=True,
            )
            app._saw_delta = False
            app._apply_chat_update(update)
            assert app._thinking is True
