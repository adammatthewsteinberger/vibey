# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Parse ``--json`` / ``--json-file`` bodies for the generated API commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json_payload(*, inline: str | None, json_file: Path | None) -> dict[str, Any]:
    if inline is not None and json_file is not None:
        msg = "pass only one of --json or --json-file, not both"
        raise ValueError(msg)
    if json_file is not None:
        text = json_file.read_text(encoding="utf-8").strip()
        if text.startswith("@"):
            path = Path(text[1:]).expanduser()
            text = path.read_text(encoding="utf-8")
        inline = text
    if inline is None:
        return {}
    data = json.loads(inline)
    if not isinstance(data, dict):
        msg = "request JSON must be an object at the top level"
        raise TypeError(msg)
    return data
