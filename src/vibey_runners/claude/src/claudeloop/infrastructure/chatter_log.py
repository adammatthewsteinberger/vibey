# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Helpers for emitting chatter.* events at the configured verbosity."""

from __future__ import annotations

import json
from typing import Any

from claudeloop.domain.chatter import chatter_event_payload


def chatter_payload(
    text: str,
    *,
    mode: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Build a chatter payload for the given mode, or None when off."""
    return chatter_event_payload(text, mode=mode, extra=extra)


def summarize_tool(name: str, raw: object, *, mode: str) -> dict[str, Any] | None:
    if mode == "off":
        return None
    try:
        rendered = raw if isinstance(raw, str) else json.dumps(raw, default=str)
    except TypeError:
        rendered = repr(raw)
    return chatter_payload(rendered, mode=mode, extra={"name": name})
