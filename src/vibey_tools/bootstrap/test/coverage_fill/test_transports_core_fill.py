"""The buffered-shipper base, the registry, and the file/sumologic transports.

`_BufferedShipper` is the shared spine of every transport, so its guarantee — that a
handler which cannot ship still cannot raise into the caller — is worth testing directly
rather than only through its subclasses.
"""

from __future__ import annotations

import atexit
import logging
import os
from unittest.mock import MagicMock, patch

import pytest

import vibey_bootstrap.transports as registry
from vibey_bootstrap.transports import builtins as builtins_mod
from vibey_bootstrap.transports import file as file_mod
from vibey_bootstrap.transports import sumologic as sumo_mod
from vibey_bootstrap.transports._base import ShipResult, _BufferedShipper


def record(msg: str = "hi") -> logging.LogRecord:
    return logging.LogRecord("svc", logging.INFO, __file__, 1, msg, None, None)


class Shipper(_BufferedShipper):
    """A shipper that records what it was asked to send, and can be told to fail."""

    _THREAD_NAME = "test-shipper"

    def __init__(self, **kw):
        kw.setdefault("counter_prefix", "test")
        kw.setdefault("flush_interval", 3600.0)
        super().__init__(**kw)
        self.shipped: list[list[str]] = []
        self.ship_error: Exception | None = None
        self.close_error: Exception | None = None

    def _ship(self, batch):
        if self.ship_error:
            raise self.ship_error
        self.shipped.append(batch)
        return ShipResult(ok=True, count=len(batch))

    def _on_close(self):
        if self.close_error:
            raise self.close_error


# ═════════════════════════════════════════════════════ _BufferedShipper


def test_a_record_the_formatter_rejects_is_handled_not_raised():
    h = Shipper()
    try:
        h.setFormatter(MagicMock(**{"format.side_effect": RuntimeError("bad formatter")}))
        handled = MagicMock()
        h.handleError = handled
        h.emit(record())
        handled.assert_called_once()
    finally:
        h.close()


def test_an_explicit_flush_swallows_a_shipping_failure():
    h = Shipper()
    try:
        h.emit(record())
        h.ship_error = RuntimeError("endpoint down")
        h.flush()  # must not raise
    finally:
        h.ship_error = None
        h.close()


def test_close_survives_a_final_drain_that_fails_and_still_runs_on_close():
    h = Shipper()
    h.emit(record())
    h.ship_error = RuntimeError("endpoint down")
    h.close()  # must not raise
    assert h._closed


def test_close_survives_its_own_on_close_hook_failing():
    h = Shipper()
    h.close_error = RuntimeError("resource already released")
    h.close()  # must not raise


def test_close_survives_an_atexit_hook_that_was_already_unregistered(monkeypatch):
    h = Shipper()
    monkeypatch.setattr(atexit, "unregister", MagicMock(side_effect=RuntimeError("gone")))
    h.close()  # must not raise


def test_close_is_idempotent():
    h = Shipper()
    h.close()
    h.close()  # the second call returns immediately


def test_the_background_loop_survives_a_shipping_failure():
    h = Shipper(flush_interval=0.1)
    try:
        h.ship_error = RuntimeError("endpoint down")
        h.emit(record())
        h._flush_now.set()
        # The thread must still be alive after swallowing the failure.
        h._flush_thread.join(timeout=1.0)
        assert h._flush_thread.is_alive()
    finally:
        h.ship_error = None
        h.close()


# ═════════════════════════════════════════════════════════════ registry


@pytest.fixture
def clean_registry():
    registry._reset_transports()
    yield
    registry._reset_transports()


def test_re_registering_a_live_transport_disables_the_running_one(clean_registry):
    first = MagicMock(spec=logging.Handler)
    registry.register_transport("t", lambda: first)
    assert registry.enable_transport("t")

    registry.register_transport("t", lambda: MagicMock(spec=logging.Handler), replace=True)
    first.close.assert_called_once()
    assert "t" not in registry._active


def test_a_factory_that_raises_leaves_the_transport_disabled(clean_registry, caplog):
    registry.register_transport("t", MagicMock(side_effect=RuntimeError("no credentials")))
    with caplog.at_level(logging.DEBUG):
        assert registry.enable_transport("t") is False
    assert "factory raised" in caplog.text
    assert "t" not in registry._active


def test_disabling_a_transport_whose_handler_will_not_close_still_removes_it(clean_registry):
    handler = MagicMock(spec=logging.Handler)
    handler.close.side_effect = RuntimeError("already closed")
    registry.register_transport("t", lambda: handler)
    registry.enable_transport("t")

    assert registry.disable_transport("t") is True
    assert "t" not in registry._active


# ═══════════════════════════════════════════════════ app-insights builtin


def test_app_insights_is_skipped_when_the_telemetry_module_is_unavailable(monkeypatch):
    import builtins as py_builtins

    real_import = py_builtins.__import__

    def refuse(name, *a, **kw):
        if name == "vibey_bootstrap.services" or "telemetry" in name:
            raise ImportError("no telemetry")
        return real_import(name, *a, **kw)

    monkeypatch.setattr(py_builtins, "__import__", refuse)
    assert builtins_mod.make_app_insights_handler() is None


def test_app_insights_is_skipped_when_configuring_it_raises(monkeypatch):
    from vibey_bootstrap.services import telemetry

    monkeypatch.setattr(telemetry, "TELEMETRY_AVAILABLE", True, raising=False)
    manager = MagicMock()
    manager.configure.side_effect = RuntimeError("connection string rejected")
    monkeypatch.setattr(telemetry, "telemetry_manager", manager, raising=False)
    assert builtins_mod.make_app_insights_handler() is None


def test_app_insights_yields_nothing_when_otel_attaches_no_handler(monkeypatch):
    from vibey_bootstrap.services import telemetry

    monkeypatch.setattr(telemetry, "TELEMETRY_AVAILABLE", True, raising=False)
    monkeypatch.setattr(telemetry, "telemetry_manager", MagicMock(), raising=False)
    # configure() succeeded but added nothing to root: a soft no-op, not a failure.
    assert builtins_mod.make_app_insights_handler() is None


# ═════════════════════════════════════════════════════════════════ file


def wrapped_file_handler() -> tuple[object, MagicMock]:
    inner = MagicMock(spec=logging.Handler)
    inner.formatter = None
    inner.level = logging.INFO
    inner.filters = []
    return file_mod._CountingFileHandler(inner), inner


def test_the_file_wrapper_survives_an_inner_handler_that_fails_on_every_call():
    handler, inner = wrapped_file_handler()
    inner.handleError.side_effect = RuntimeError("stderr is closed")
    inner.flush.side_effect = RuntimeError("disk full")
    inner.close.side_effect = RuntimeError("already closed")

    handler.handleError(record())  # must not raise
    handler.flush()  # must not raise
    handler.close()  # must not raise


def test_a_log_path_that_cannot_be_opened_disables_the_file_transport(
    monkeypatch, caplog, tmp_path
):
    monkeypatch.setenv("FILE_LOG_PATH", str(tmp_path / "app.log"))
    with (
        patch.object(
            file_mod.logging.handlers,
            "RotatingFileHandler",
            side_effect=OSError("read-only filesystem"),
        ),
        caplog.at_level(logging.WARNING),
    ):
        assert file_mod.make_file_handler() is None
    assert "could not open log file" in caplog.text


def test_a_filesystem_that_refuses_chmod_does_not_disable_the_transport(monkeypatch, tmp_path):
    monkeypatch.setenv("FILE_LOG_PATH", str(tmp_path / "app.log"))
    monkeypatch.setattr(os, "chmod", MagicMock(side_effect=OSError("unsupported")))
    handler = file_mod.make_file_handler()
    assert handler is not None
    handler.close()


def test_time_based_rotation_is_selected_by_configuration(monkeypatch, tmp_path):
    monkeypatch.setenv("FILE_LOG_PATH", str(tmp_path / "app.log"))
    monkeypatch.setenv("FILE_LOG_ROTATION", "time")
    monkeypatch.setenv("FILE_LOG_WHEN", "H")
    handler = file_mod.make_file_handler()
    try:
        assert isinstance(handler._inner, logging.handlers.TimedRotatingFileHandler)
        assert handler._inner.when == "H"
    finally:
        handler.close()


# ════════════════════════════════════════════════════════════ sumologic


def test_closing_sumologic_survives_a_session_that_will_not_close():
    session = MagicMock()
    session.close.side_effect = RuntimeError("socket already gone")
    with patch.object(sumo_mod, "_build_session", return_value=session):
        h = sumo_mod.SumoLogicHandler(
            endpoint_url="https://collect.example.com", flush_interval=3600.0
        )
    h.close()  # must not raise
    session.close.assert_called_once()


def test_sumologic_ships_nothing_for_an_empty_batch():
    with patch.object(sumo_mod, "_build_session", return_value=MagicMock()) as session:
        h = sumo_mod.SumoLogicHandler(
            endpoint_url="https://collect.example.com", flush_interval=3600.0
        )
    try:
        assert h._ship([]).count == 0
        session.return_value.post.assert_not_called()
    finally:
        h.close()


@pytest.mark.parametrize(
    "resolver, default, expected",
    [
        (sumo_mod._int_env, 200, 200),
        (sumo_mod._float_env, 5.0, 5.0),
    ],
)
def test_sumologic_env_helpers_fall_back_on_junk(monkeypatch, resolver, default, expected):
    monkeypatch.setenv("SUMO_X", "junk")
    assert resolver("SUMO_X", default) == expected


class BrittleShipper(Shipper):
    """A shipper whose own buffer handling is broken — the case the outer guards exist for.

    `_drain_and_ship` already absorbs anything `_ship` throws, so the only way to reach
    the guards around it is for the drain machinery itself to fail.
    """

    _THREAD_NAME = "brittle-shipper"

    def _take_batch(self):
        raise RuntimeError("the buffer is corrupt")


def test_flush_survives_a_drain_that_cannot_even_read_the_buffer():
    h = BrittleShipper()
    try:
        h.flush()  # must not raise
    finally:
        h.close()  # nor must this


def test_the_background_loop_survives_a_drain_that_cannot_read_the_buffer():
    h = BrittleShipper(flush_interval=0.1)
    try:
        h._flush_now.set()
        h._flush_thread.join(timeout=1.0)
        assert h._flush_thread.is_alive()  # it looped, swallowed, and kept going
    finally:
        h.close()
