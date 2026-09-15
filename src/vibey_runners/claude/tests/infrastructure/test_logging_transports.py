# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Dual console + optional file logging transports."""

from __future__ import annotations

import io
import json
import logging
import sys
from pathlib import Path

from claudeloop.infrastructure.logging import configure_logging, get_logger
from claudeloop.infrastructure.redact import REDACTED_VALUE


def _capture_configure(*, log_file: Path | None, level: str = "INFO") -> str:
    buf = io.StringIO()
    old = sys.stderr
    sys.stderr = buf
    try:
        configure_logging(log_file=log_file, level=level)
        get_logger(component="unit").info(
            "sample.event",
            api_key="sk-ant-abcdefghijklmnopqrstuvwxyz012345",
            ok=True,
        )
    finally:
        sys.stderr = old
    return buf.getvalue()


def test_dual_console_emits_human_and_json() -> None:
    text = _capture_configure(log_file=None)
    assert "sample.event" in text
    json_lines = [json.loads(line) for line in text.splitlines() if line.startswith("{")]
    assert len(json_lines) >= 1
    payload = json_lines[0]
    assert payload["event"] == "sample.event"
    assert payload["transport"] == "console_json"
    assert payload["api_key"] == REDACTED_VALUE
    assert "sk-ant-" not in text


def test_file_transport_independent(tmp_path: Path) -> None:
    path = tmp_path / "structlog.jsonl"
    text = _capture_configure(log_file=path)
    assert path.is_file()
    file_lines = [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    assert file_lines
    assert file_lines[0]["transport"] == "file"
    assert file_lines[0]["api_key"] == REDACTED_VALUE
    # console still dual
    assert any(line.startswith("{") for line in text.splitlines())


def test_level_filtering_drops_debug_at_info() -> None:
    buf = io.StringIO()
    old = sys.stderr
    sys.stderr = buf
    try:
        configure_logging(log_file=None, level="INFO")
        log = get_logger(component="unit")
        log.debug("should.not.appear")
        log.info("should.appear")
    finally:
        sys.stderr = old
    text = buf.getvalue()
    assert "should.appear" in text
    assert "should.not.appear" not in text


def test_root_handler_count_with_and_without_file(tmp_path: Path) -> None:
    configure_logging(log_file=None, level="INFO")
    assert len(logging.getLogger().handlers) == 2
    configure_logging(log_file=tmp_path / "x.jsonl", level="INFO")
    assert len(logging.getLogger().handlers) == 3
