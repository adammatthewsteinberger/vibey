"""File transport tests."""

from __future__ import annotations

import logging
from pathlib import Path

from vibey_bootstrap.transports.file import make_file_handler


def test_make_file_handler_writes_json(tmp_path: Path, monkeypatch) -> None:
    log_path = tmp_path / "app.jsonl"
    monkeypatch.setenv("FILE_LOG_PATH", str(log_path))
    handler = make_file_handler()
    assert handler is not None
    try:
        rec = logging.LogRecord("svc", logging.INFO, __file__, 1, "hello", None, None)
        handler.emit(rec)
        handler.flush()
    finally:
        handler.close()
    assert log_path.exists()
    assert "hello" in log_path.read_text()


def test_make_file_handler_returns_none_without_path(monkeypatch) -> None:
    monkeypatch.delenv("FILE_LOG_PATH", raising=False)
    assert make_file_handler() is None
