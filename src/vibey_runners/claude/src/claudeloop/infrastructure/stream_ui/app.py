# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Textual StreamApp — multi-pane live / follow / replay UI.

Left pane is a continuous realtime AI chat log (prompts + streamed tokens).
Prompts are never cleared or cropped for display: event payloads carry full
``text``, and each new turn appends rather than wiping the panel.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from textual.app import App, ComposeResult, ScreenStackError
from textual.containers import Horizontal
from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.widgets import Footer, Header, RichLog, Static

from claudeloop.infrastructure.stream_ui import BufferingStreamUi, StreamUiState


@dataclass
class ChatUpdate:
    """Pure description of how one event should mutate the chat panes."""

    clear: bool = False
    assistant_lines: list[str] = field(default_factory=list)
    tool_lines: list[str] = field(default_factory=list)
    saw_delta: bool = False
    header_dirty: bool = False


def _payload_text(payload: dict[str, Any]) -> str:
    """Prefer full ``text``; fall back to ``preview`` for older event files."""
    text = payload.get("text")
    if isinstance(text, str) and text:
        return text
    preview = payload.get("preview")
    return str(preview) if preview is not None else ""


def chat_update_for_record(
    record: dict[str, Any],
    *,
    saw_delta: bool = False,
    clear_on_prompt: bool = False,
) -> ChatUpdate:
    """Map an events.jsonl record to chat-pane updates.

    ``clear_on_prompt`` is only for replay turn-jump navigation. Live/follow
    keep a continuous transcript (clear_on_prompt=False).
    """
    et = record.get("event_type")
    payload = record.get("payload") or {}
    if not isinstance(payload, dict):
        payload = {}
    update = ChatUpdate(saw_delta=saw_delta, header_dirty=True)

    if et == "chatter.delta":
        text = str(payload.get("text") or "")
        if text:
            update.assistant_lines.append(text)
        update.saw_delta = True
    elif et == "chatter.prompt":
        update.clear = clear_on_prompt
        update.saw_delta = False
        body = _payload_text(payload)
        update.assistant_lines.append(f"\n[dim]── prompt ──[/dim]\n{body}\n\n")
    elif et == "chatter.assistant":
        if saw_delta:
            return update
        body = _payload_text(payload)
        if body:
            update.assistant_lines.append(body)
            if not body.endswith("\n"):
                update.assistant_lines.append("\n")
        update.saw_delta = True
    elif et == "chatter.tool":
        name = payload.get("name") or "tool"
        preview = _payload_text(payload) or payload.get("preview") or ""
        update.tool_lines.append(f"{name}: {preview}")
    return update


class StreamApp(App[None]):
    CSS = """
    #header-bar { height: 3; dock: top; }
    #thinking-bar { height: 1; dock: top; display: none; color: $text-muted; }
    #assistant {
        height: 1fr;
        width: 1fr;
        border: solid $accent;
        overflow-x: auto;
        overflow-y: auto;
    }
    #tools { width: 36%; border: solid $primary; }
    #main { height: 1fr; }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("p", "toggle_pause", "Pause follow"),
        ("space", "toggle_play", "Play/Pause replay"),
        ("[", "prev_turn", "Prev turn"),
        ("]", "next_turn", "Next turn"),
    ]

    paused: reactive[bool] = reactive(False)

    def __init__(
        self,
        *,
        events_path: Path,
        follow: bool = True,
        replay: bool = False,
        speed: float = 1.0,
        initial: StreamUiState | None = None,
        live_source: BufferingStreamUi | None = None,
    ) -> None:
        super().__init__()
        self.events_path = events_path
        self.follow = follow
        self.replay = replay
        self.speed = speed
        self.state = initial or StreamUiState()
        self.live_source = live_source
        self._offset = 0
        self._records: list[dict[str, Any]] = []
        self._replay_index = 0
        self._turn_starts: list[int] = []
        self._playing = True
        self._saw_delta = False
        self._thinking = False
        self._thinking_frame = 0
        self._ui_mounted = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static(self._header_text(), id="header-bar")
        yield Static("", id="thinking-bar")
        with Horizontal(id="main"):
            # wrap=True so long prompts are never horizontally cropped.
            yield RichLog(id="assistant", highlight=True, markup=True, wrap=True, auto_scroll=True)
            yield RichLog(id="tools", highlight=True, markup=True, wrap=True, auto_scroll=True)
        yield Footer()

    def on_mount(self) -> None:
        self._ui_mounted = True

    def on_ready(self) -> None:
        """Start the periodic ticks only once the DOM is fully composed.

        on_mount fires before child widgets finish mounting, and a 50ms replay
        tick could beat #assistant into existence — query_one then raised
        NoMatches, seen as intermittent failures across Python versions in
        tests and as a crash risk on any slow terminal. on_ready is Textual's
        guarantee that every composed widget exists and the first frame has
        painted, which is exactly the precondition every tick relies on.
        """
        if self.replay:
            self._load_all()
            self.set_interval(0.05, self._tick_replay)
        else:
            self.set_interval(0.2, self._tick_follow)
            if self.live_source is not None:
                self.set_interval(0.1, self._tick_live)
        self.set_interval(0.5, self._tick_thinking)

    def on_unmount(self) -> None:
        """Prevent periodic callbacks from touching widgets during teardown."""
        self._ui_mounted = False

    def _set_thinking(self, active: bool) -> None:
        self._thinking = active
        bar = self.query_one("#thinking-bar", Static)
        if active:
            bar.styles.display = "block"
            self._thinking_frame = 0
            bar.update("thinking.")
        else:
            bar.styles.display = "none"
            bar.update("")

    def _tick_thinking(self) -> None:
        if not self._thinking:
            return
        self._thinking_frame = (self._thinking_frame + 1) % 3
        dots = "." * (self._thinking_frame + 1)
        self.query_one("#thinking-bar", Static).update(f"thinking{dots}")

    def _header_text(self) -> str:
        s = self.state
        return (
            f"run={s.run_id}  trace={s.trace_id}  model={s.model}  "
            f"effort={s.effort}  attempt={s.attempt}  phase={s.phase}  "
            f"spend=${s.spend:.4f}"
        )

    def _refresh_header(self) -> None:
        self.query_one("#header-bar", Static).update(self._header_text())

    def _append_assistant(self, text: str) -> None:
        if text:
            self.query_one("#assistant", RichLog).write(text)

    def _append_tool(self, line: str) -> None:
        self.query_one("#tools", RichLog).write(line)

    def _apply_chat_update(self, update: ChatUpdate) -> None:
        if update.clear:
            self.query_one("#assistant", RichLog).clear()
        for line in update.assistant_lines:
            self._append_assistant(line)
        for line in update.tool_lines:
            self._append_tool(line)
        # Prompt sets saw_delta=False → show thinking; delta/assistant True → hide.
        if update.saw_delta:
            self._set_thinking(False)
        elif update.assistant_lines and not self._saw_delta:
            # Fresh prompt lines without prior tokens this turn.
            self._set_thinking(True)
        self._saw_delta = update.saw_delta
        if update.header_dirty:
            self._refresh_header()

    def _load_all(self) -> None:
        if not self.events_path.is_file():
            return
        self._records = []
        self._turn_starts = []
        with self.events_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if record.get("event_type") == "chatter.prompt":
                    self._turn_starts.append(len(self._records))
                self._records.append(record)
        if not self._turn_starts and self._records:
            self._turn_starts = [0]

    def _apply_record(self, record: dict[str, Any], *, clear_on_prompt: bool = False) -> None:
        if record.get("trace_id"):
            self.state.trace_id = str(record["trace_id"])
        if record.get("run_id"):
            self.state.run_id = str(record["run_id"])
        et = record.get("event_type")
        payload = record.get("payload") or {}
        if et == "model.profile_changed" and isinstance(payload, dict):
            self.state.model = str(payload.get("model") or self.state.model)
            self.state.effort = str(payload.get("effort") or self.state.effort)
        elif et == "turn.starting":
            attempt = record.get("attempt")
            if isinstance(attempt, int):
                self.state.attempt = attempt
        update = chat_update_for_record(
            record,
            saw_delta=self._saw_delta,
            clear_on_prompt=clear_on_prompt,
        )
        self._apply_chat_update(update)

    def _tick_follow(self) -> None:
        if self.paused or not self.follow:
            return
        if not self.events_path.is_file():
            return
        with self.events_path.open("r", encoding="utf-8") as fh:
            fh.seek(self._offset)
            chunk = fh.read()
            self._offset = fh.tell()
        for line in chunk.splitlines():
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            et = record.get("event_type")
            # Live path already paints chat via BufferingStreamUi — avoid dupes.
            if self.live_source is not None and isinstance(et, str) and et.startswith("chatter."):
                if et == "chatter.tool":
                    self._apply_record(record)
                continue
            self._apply_record(record)

    def _tick_live(self) -> None:
        if not self._ui_mounted or self.live_source is None or self.paused:
            return
        # Textual may dispatch an interval after ``on_mount`` has begun but
        # before every composed child is attached (and likewise while a screen
        # is being replaced). Do not consume buffered model output until all
        # widgets touched by this tick are available; the next interval can
        # safely retry it.
        try:
            self.query_one("#header-bar", Static)
            self.query_one("#thinking-bar", Static)
            self.query_one("#assistant", RichLog)
        except (NoMatches, ScreenStackError):
            return
        while self.live_source.prompts:
            prompt = self.live_source.prompts.pop(0)
            self._saw_delta = False
            self._append_assistant(f"\n[dim]── prompt ──[/dim]\n{prompt}\n\n")
            self._set_thinking(True)
        while self.live_source.deltas:
            text, _turn_id, _seq = self.live_source.deltas.pop(0)
            if not self._saw_delta:
                self._set_thinking(False)
            self._saw_delta = True
            self._append_assistant(text)
        while self.live_source.assistants:
            text = self.live_source.assistants.pop(0)
            self._set_thinking(False)
            self._append_assistant(text if text.endswith("\n") else f"{text}\n")
        self.state = self.live_source.state
        self._refresh_header()

    def _tick_replay(self) -> None:
        if not self._playing or self.paused:
            return
        if self._replay_index >= len(self._records):
            return
        # Same readiness probe as _tick_live: an interval (or a test driving
        # this tick directly) can run before every composed child is attached.
        # Consume nothing until the widgets a record paints exist; the next
        # tick retries safely.
        try:
            self.query_one("#assistant", RichLog)
        except (NoMatches, ScreenStackError):
            return
        n = 1 if self.speed > 0 else 20
        for _ in range(n):
            if self._replay_index >= len(self._records):
                break
            self._apply_record(self._records[self._replay_index])
            self._replay_index += 1

    def action_toggle_pause(self) -> None:
        self.paused = not self.paused

    def action_toggle_play(self) -> None:
        if self.replay:
            self._playing = not self._playing
        else:
            self.paused = not self.paused

    def action_prev_turn(self) -> None:
        if not self.replay or not self._turn_starts:
            return
        current = self._replay_index
        prev = self._turn_starts[0]
        # Landing on a turn always leaves _replay_index one past that turn's
        # own start (see below), so comparing against the raw current index
        # re-selects the turn we're already on and repeated presses get stuck
        # there forever. Compare against current - 1 -- the turn's own start
        # -- so a press always walks to a strictly earlier turn.
        for start in self._turn_starts:
            if start < current - 1:
                prev = start
            else:
                break
        self.query_one("#assistant", RichLog).clear()
        self.query_one("#tools", RichLog).clear()
        self._saw_delta = False
        self._replay_index = prev
        self._apply_record(self._records[prev], clear_on_prompt=True)
        self._replay_index = prev + 1

    def action_next_turn(self) -> None:
        if not self.replay or not self._turn_starts:
            return
        current = self._replay_index
        nxt = None
        for start in self._turn_starts:
            if start >= current:
                nxt = start
                break
        if nxt is None:
            return
        self.query_one("#assistant", RichLog).clear()
        self.query_one("#tools", RichLog).clear()
        self._saw_delta = False
        self._replay_index = nxt
        self._apply_record(self._records[nxt], clear_on_prompt=True)
        self._replay_index = nxt + 1
