# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Textual multi-pane stream UI — live, follow, and historical replay."""

from __future__ import annotations

import json
import sys
import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class StreamUiState:
    run_id: str = ""
    trace_id: str = ""
    model: str = ""
    effort: str = ""
    attempt: int = 0
    phase: str = ""
    spend: float = 0.0
    assistant: str = ""
    tools: list[str] = field(default_factory=list)


class NullStreamUi:
    def on_delta(self, text: str, *, turn_id: str, seq: int) -> None:
        del text, turn_id, seq

    def on_turn_boundary(self, *, turn_id: str, attempt: int) -> None:
        del turn_id, attempt

    def on_prompt(self, text: str) -> None:
        del text

    def on_assistant(self, text: str) -> None:
        del text

    def on_tool(self, name: str, summary: str) -> None:
        del name, summary

    def on_status(self, state: dict[str, Any]) -> None:
        del state

    def close(self) -> None:
        return None


class BufferingStreamUi:
    """In-process stream sink used when Textual is not yet running / for tests."""

    def __init__(self) -> None:
        self.state = StreamUiState()
        self.deltas: list[tuple[str, str, int]] = []
        self.prompts: list[str] = []
        self.assistants: list[str] = []
        self.closed = False
        self._saw_delta_this_turn = False

    def on_delta(self, text: str, *, turn_id: str, seq: int) -> None:
        self.deltas.append((text, turn_id, seq))
        self.state.assistant += text
        self._saw_delta_this_turn = True

    def on_turn_boundary(self, *, turn_id: str, attempt: int) -> None:
        del turn_id
        self.state.attempt = attempt
        self._saw_delta_this_turn = False

    def on_prompt(self, text: str) -> None:
        self.prompts.append(text)
        self._saw_delta_this_turn = False

    def on_assistant(self, text: str) -> None:
        # When tokens already streamed this turn, skip duplicating the final blob.
        if self._saw_delta_this_turn:
            return
        if text:
            self.assistants.append(text)
            self.state.assistant += text

    def on_tool(self, name: str, summary: str) -> None:
        self.state.tools.append(f"{name}: {summary}")
        self.state.tools = self.state.tools[-50:]

    def on_status(self, state: dict[str, Any]) -> None:
        if "model" in state:
            self.state.model = str(state["model"])
        if "effort" in state:
            self.state.effort = str(state["effort"])
        if "phase" in state:
            self.state.phase = str(state["phase"])
        if "dollars_spent" in state:
            self.state.spend = float(state["dollars_spent"])
        if "run_id" in state:
            self.state.run_id = str(state["run_id"])
        if "trace_id" in state:
            self.state.trace_id = str(state["trace_id"])

    def close(self) -> None:
        self.closed = True


def iter_event_records(path: Path) -> Iterator[dict[str, Any]]:
    if not path.is_file():
        return
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def dump_transcript(path: Path, *, file: Any = None) -> None:
    """Plain chronological transcript for non-TTY replay."""
    out = file or sys.stdout
    for record in iter_event_records(path):
        et = record.get("event_type")
        payload = record.get("payload") or {}
        if et == "chatter.delta":
            out.write(str(payload.get("text") or ""))
        elif et == "chatter.prompt":
            out.write(f"\n--- prompt ---\n{payload.get('text') or payload.get('preview')}\n")
        elif et == "chatter.assistant":
            out.write(f"\n--- assistant ---\n{payload.get('text') or payload.get('preview')}\n")
    out.write("\n")


def run_textual_app(
    *,
    events_path: Path,
    follow: bool = True,
    replay: bool = False,
    speed: float = 1.0,
    initial: StreamUiState | None = None,
    live_source: BufferingStreamUi | None = None,
) -> None:
    """Launch the full-screen Textual app (requires a TTY)."""
    from claudeloop.infrastructure.stream_ui.app import StreamApp

    if not sys.stdout.isatty():
        raise RuntimeError("stream UI requires a TTY; use --replay for a plain transcript dump")

    app = StreamApp(
        events_path=events_path,
        follow=follow,
        replay=replay,
        speed=speed,
        initial=initial or StreamUiState(),
        live_source=live_source,
    )
    app.run()


def follow_events_plain(
    path: Path,
    *,
    poll_seconds: float = 0.25,
    follow: bool = True,
) -> None:
    offset = 0
    while True:
        if path.is_file():
            with path.open("r", encoding="utf-8") as f:
                f.seek(offset)
                chunk = f.read()
                if chunk:
                    for line in chunk.splitlines():
                        try:
                            record = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        et = record.get("event_type")
                        payload = record.get("payload") or {}
                        if et == "chatter.delta":
                            sys.stdout.write(str(payload.get("text") or ""))
                            sys.stdout.flush()
                        elif et and str(et).startswith("chatter."):
                            body = payload.get("text") or payload.get("preview") or ""
                            sys.stdout.write(f"\n[{et}] {body}\n")
                            sys.stdout.flush()
                    offset = f.tell()
        if not follow:
            return
        time.sleep(poll_seconds)
