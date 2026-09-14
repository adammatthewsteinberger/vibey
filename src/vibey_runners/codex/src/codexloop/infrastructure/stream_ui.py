# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Optional Textual live token view (``--stream-ui``).

!!! note "Roadmap"
    Full token streaming against a live app-server session is still experimental.
    This module ships a minimal Textual shell that tails a JSONL event file so
    ``watch --replay`` and ``--stream-ui`` have a working path today.
"""

from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, RichLog


class StreamUiApp(App[None]):
    """Tail a JSONL event log in a Textual window."""

    CSS = """
    RichLog { height: 1fr; }
    """

    def __init__(self, path: Path) -> None:
        super().__init__()
        self._path = path

    def compose(self) -> ComposeResult:
        yield Header()
        yield RichLog(id="log", highlight=True, markup=False)
        yield Footer()

    def on_mount(self) -> None:
        log = self.query_one("#log", RichLog)
        if not self._path.is_file():
            log.write(f"(no events yet at {self._path})")
            return
        for line in self._path.read_text(encoding="utf-8").splitlines():
            log.write(line)


def run_stream_ui(path: Path) -> None:  # pragma: no cover — interactive TUI entry
    """Blocking entry used by the CLI ``--stream-ui`` flag."""
    StreamUiApp(path).run()
