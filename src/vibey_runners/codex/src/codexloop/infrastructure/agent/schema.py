# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""JSON Schema for structured completion verdicts (R12)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final

COMPLETION_OUTPUT_SCHEMA: Final[dict[str, object]] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "CodexloopCompletionVerdict",
    "type": "object",
    "additionalProperties": False,
    "required": ["complete", "remaining_work", "blocked_on", "summary"],
    "properties": {
        "complete": {"type": "boolean"},
        "remaining_work": {
            "type": "array",
            "items": {"type": "string"},
        },
        "blocked_on": {"type": ["string", "null"]},
        "summary": {"type": "string"},
    },
}


def write_output_schema(path: str | Path) -> Path:
    """Write the completion JSON Schema to ``path`` and return that path."""
    dest = Path(path)
    dest.write_text(json.dumps(COMPLETION_OUTPUT_SCHEMA, indent=2) + "\n", encoding="utf-8")
    return dest
