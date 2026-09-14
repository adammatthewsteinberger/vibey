# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Textual stream UI — live, follow, and historical replay of events.jsonl."""

from __future__ import annotations

import json
import sys
import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, RichLog


@dataclass
class StreamUiState:
    run_id: str = ""
    attempt: int = 0
    phase: str = ""
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


def iter_event_records(path: Path) -> Iterator[dict[str, Any]]:
    if not path.is_file():
        return
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def dump_transcript(path: Path, *, file: Any = None) -> None:
    out = file or sys.stdout
    for record in iter_event_records(path):
        et = record.get("event_type")
        payload = record.get("payload") or {}
        if not isinstance(payload, dict):
            payload = {}
        if et == "chatter.delta":
            out.write(str(payload.get("text") or ""))
        elif et == "chatter.prompt":
            out.write(f"\n--- prompt ---\n{payload.get('text') or payload.get('preview')}\n")
        elif et == "chatter.assistant":
            out.write(f"\n--- assistant ---\n{payload.get('text') or payload.get('preview')}\n")
    out.write("\n")


def follow_events_plain(
    path: Path,
    *,
    poll_seconds: float = 0.25,
    follow: bool = True,
) -> None:
    offset = 0
    while True:
        if path.is_file():
            with path.open("r", encoding="utf-8") as handle:
                handle.seek(offset)
                chunk = handle.read()
                if chunk:
                    for line in chunk.splitlines():
                        try:
                            record = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        et = record.get("event_type")
                        payload = record.get("payload") or {}
                        if not isinstance(payload, dict):
                            payload = {}
                        if et == "chatter.delta":
                            sys.stdout.write(str(payload.get("text") or ""))
                            sys.stdout.flush()
                        elif et and str(et).startswith("chatter."):
                            body = payload.get("text") or payload.get("preview") or ""
                            sys.stdout.write(f"\n[{et}] {body}\n")
                            sys.stdout.flush()
                    offset = handle.tell()
        if not follow:
            return
        time.sleep(poll_seconds)


class StreamApp(App[None]):
    """Minimal full-screen tail of events.jsonl."""

    CSS = "RichLog { height: 1fr; }"

    def __init__(
        self,
        *,
        events_path: Path,
        follow: bool = True,
        replay: bool = False,
        speed: float = 1.0,
    ) -> None:
        super().__init__()
        self._events_path = events_path
        self._follow = follow
        self._replay = replay
        self._speed = speed
        self._offset = 0
        self._saw_delta = False

    def compose(self) -> ComposeResult:
        yield Header()
        yield RichLog(id="stream", highlight=True, markup=True)
        yield Footer()

    def on_mount(self) -> None:
        if self._replay:
            self._drain(follow=False)
        self.set_interval(0.25, self._tick)

    def _tick(self) -> None:
        self._drain(follow=self._follow)

    def _drain(self, *, follow: bool) -> None:
        log = self.query_one("#stream", RichLog)
        if not self._events_path.is_file():
            return
        with self._events_path.open("r", encoding="utf-8") as handle:
            handle.seek(self._offset)
            chunk = handle.read()
            self._offset = handle.tell()
        for line in chunk.splitlines():
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            et = record.get("event_type")
            payload = record.get("payload") or {}
            if not isinstance(payload, dict):
                payload = {}
            if et == "chatter.delta":
                text = str(payload.get("text") or "")
                if text:
                    log.write(text, scroll_end=True)
                self._saw_delta = True
            elif et == "chatter.prompt":
                self._saw_delta = False
                body = payload.get("text") or payload.get("preview") or ""
                log.write(f"\n[dim]── prompt ──[/dim]\n{body}\n", scroll_end=True)
            elif et == "chatter.assistant":
                if self._saw_delta:
                    continue
                body = payload.get("text") or payload.get("preview") or ""
                if body:
                    log.write(str(body), scroll_end=True)
            elif et == "chatter.tool":
                name = payload.get("name") or "tool"
                summary = str(payload.get("summary") or "")
                log.write(f"[yellow]{name}[/yellow] {summary}", scroll_end=True)
            elif et:
                log.write(f"[dim]{et}[/dim]", scroll_end=True)
        if not follow:
            return
        del follow


def run_textual_app(
    *,
    events_path: Path,
    follow: bool = True,
    replay: bool = False,
    speed: float = 1.0,
) -> None:
    if not sys.stdout.isatty():
        if replay:
            dump_transcript(events_path)
            return
        raise RuntimeError("stream UI requires a TTY; use --replay for a plain transcript dump")
    StreamApp(
        events_path=events_path,
        follow=follow and not replay,
        replay=replay,
        speed=speed,
    ).run()
