# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

import inspect

from cursorloop.infrastructure import redact
from cursorloop.infrastructure.redact import redact_event


def test_cursor_api_keys_are_scrubbed_by_pattern_not_just_by_key_name() -> None:
    """Cursor's fixed crsr_ prefix makes a pattern scrub genuinely effective —
    which matters because debug logging is a stated requirement and this tool
    handles credentials by design."""
    event = {"message": "auth failed for crsr_abcdefghijklmnopqrstuvwxyz012345"}
    assert "crsr_abcdefghij" not in redact_event(None, "info", event)["message"]


def test_known_secret_keys_are_scrubbed() -> None:
    event = {
        "api_key": "crsr_x",
        "CURSOR_API_KEY": "crsr_y",
        "Authorization": "Bearer crsr_z",
        "client_secret": "s",
        "safe": "keep me",
    }
    scrubbed = redact_event(None, "info", event)
    assert scrubbed["safe"] == "keep me"
    for key in ("api_key", "CURSOR_API_KEY", "Authorization", "client_secret"):
        assert scrubbed[key] == "***"


def test_no_anthropic_key_patterns_are_referenced() -> None:
    assert "sk-ant" not in inspect.getsource(redact)
