# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Doctor use case — offline error classification (stdlib + domain only)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from cursorloop.domain.classify import TurnSignals, classify


def explain_error_payload(path: Path) -> str:
    """Re-run classify() offline against a captured terminal-error payload."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("payload must be a JSON object")
    signals = TurnSignals(
        error_type=None if raw.get("error_type") is None else str(raw.get("error_type")),
        error_code=None if raw.get("error_code") is None else str(raw.get("error_code")),
        proto_error_code=(
            None if raw.get("proto_error_code") is None else str(raw.get("proto_error_code"))
        ),
        error_message=str(raw.get("error_message", raw.get("message", ""))),
        http_status=raw.get("http_status") if isinstance(raw.get("http_status"), int) else None,
        is_retryable=raw.get("is_retryable") if isinstance(raw.get("is_retryable"), bool) else None,
        retry_after=None if raw.get("retry_after") is None else str(raw.get("retry_after")),
        run_status=None if raw.get("run_status") is None else str(raw.get("run_status")),
        result_text=str(raw.get("result_text", raw.get("result", ""))),
    )
    result = classify(signals, now=datetime.now(UTC))
    return type(result).__name__
