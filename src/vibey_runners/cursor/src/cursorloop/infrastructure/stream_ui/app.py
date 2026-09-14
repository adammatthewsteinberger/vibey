# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Textual stream UI sketch — fed from on_delta / on_step (M5)."""

from __future__ import annotations

from typing import Any


class StreamUiApp:
    """Minimal stand-in for the full-screen Textual app.

    Production watch will mount a Textual Application; this class keeps the
    port-shaped callbacks so runners and tests can attach without requiring a
    TTY. Importing textual is deferred to ``run()`` so headless CI stays light.
    """

    def __init__(self) -> None:
        self.deltas: list[str] = []
        self.steps: list[dict[str, Any]] = []
        self._running = False

    def on_delta(self, text: str) -> None:
        self.deltas.append(text)

    def on_step(self, payload: dict[str, Any]) -> None:
        self.steps.append(dict(payload))

    def run(self) -> None:
        """Launch Textual when a real TTY is available; otherwise no-op."""
        try:
            from textual.app import App, ComposeResult
            from textual.widgets import RichLog
        except ImportError:
            return

        deltas = list(self.deltas)
        steps = list(self.steps)

        class _WatchApp(App[None]):
            CSS = "RichLog { height: 1fr; }"

            def compose(self) -> ComposeResult:
                yield RichLog(id="stream")

            def on_mount(self) -> None:
                log = self.query_one("#stream", RichLog)
                for step in steps:
                    log.write(f"[step] {step}")
                for delta in deltas:
                    log.write(delta)

        self._running = True
        _WatchApp().run()
        self._running = False
