"""Exhaustive file transport tests."""

from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import patch

from vibey_bootstrap.counters import counter_snapshot
from vibey_bootstrap.transports.file import _CountingFileHandler, make_file_handler


def test_file_handler_records_counter(tmp_path: Path, monkeypatch) -> None:
    log_path = tmp_path / "app.jsonl"
    monkeypatch.setenv("FILE_LOG_PATH", str(log_path))
    handler = make_file_handler()
    assert handler is not None
    before = counter_snapshot().get("file.transport.records", 0)
    try:
        handler.emit(logging.LogRecord("s", logging.INFO, __file__, 1, "hello", None, None))
        handler.flush()
    finally:
        handler.close()
    assert counter_snapshot().get("file.transport.records", 0) == before + 1
    assert "hello" in log_path.read_text()


def test_file_handler_size_rotation(tmp_path: Path, monkeypatch) -> None:
    log_path = tmp_path / "rot.jsonl"
    monkeypatch.setenv("FILE_LOG_PATH", str(log_path))
    monkeypatch.setenv("FILE_LOG_ROTATION", "size")
    monkeypatch.setenv("FILE_LOG_MAX_BYTES", "100")
    handler = make_file_handler()
    assert handler is not None
    handler.close()


def test_file_handler_rejects_escape(tmp_path: Path, monkeypatch) -> None:
    log_path = tmp_path / "safe" / "app.jsonl"
    monkeypatch.setenv("FILE_LOG_PATH", str(log_path))
    monkeypatch.setenv("FILE_LOG_ROOT", str(tmp_path / "other"))
    assert make_file_handler() is None


def test_file_handler_makedirs_failure(tmp_path: Path, monkeypatch) -> None:
    log_path = tmp_path / "nested" / "deep" / "app.jsonl"
    monkeypatch.setenv("FILE_LOG_PATH", str(log_path))
    with patch("vibey_bootstrap.transports.file.os.makedirs", side_effect=OSError("denied")):
        assert make_file_handler() is None


def test_counting_wrapper_handle_error_bumps_counter() -> None:
    inner = logging.Handler()
    inner.emit = lambda r: (_ for _ in ()).throw(RuntimeError("fail"))  # type: ignore[method-assign]
    wrapper = _CountingFileHandler(inner)
    before = counter_snapshot().get("file.transport.error", 0)
    wrapper.emit(logging.LogRecord("s", logging.INFO, __file__, 1, "x", None, None))
    assert counter_snapshot().get("file.transport.error", 0) == before + 1


def test_invalid_int_env_fallback(tmp_path: Path, monkeypatch) -> None:
    log_path = tmp_path / "app.jsonl"
    monkeypatch.setenv("FILE_LOG_PATH", str(log_path))
    monkeypatch.setenv("FILE_LOG_MAX_BYTES", "not-a-number")
    handler = make_file_handler()
    assert handler is not None
    handler.close()
