"""Registry behavior: register/enable/disable/list + reconcile + idempotency."""

from __future__ import annotations

import logging

import pytest

import vibey_bootstrap.transports as transports
from vibey_bootstrap.transports import (
    disable_transport,
    enable_transport,
    list_transports,
    register_transport,
)


def _counting_factory(box: dict[str, int]):
    def factory() -> logging.Handler:
        box["built"] = box.get("built", 0) + 1
        return logging.NullHandler()

    return factory


def test_register_rejects_duplicate_without_replace() -> None:
    register_transport("custom", lambda: logging.NullHandler())
    with pytest.raises(ValueError):
        register_transport("custom", lambda: logging.NullHandler())


def test_register_replace_allowed() -> None:
    register_transport("custom", lambda: logging.NullHandler())
    register_transport("custom", lambda: logging.NullHandler(), replace=True)
    assert "custom" in list_transports()


def test_register_empty_name_rejected() -> None:
    with pytest.raises(ValueError):
        register_transport("", lambda: logging.NullHandler())


def test_enable_adds_exactly_one_handler_idempotent() -> None:
    box: dict[str, int] = {}
    register_transport("custom", _counting_factory(box))
    root = logging.getLogger()
    before = len(root.handlers)

    assert enable_transport("custom") is True
    assert enable_transport("custom") is False  # idempotent
    assert len(root.handlers) == before + 1
    assert box["built"] == 1


def test_disable_removes_and_closes() -> None:
    closed: dict[str, bool] = {}

    class _H(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover
            pass

        def close(self) -> None:
            closed["yes"] = True
            super().close()

    register_transport("custom", lambda: _H())
    root = logging.getLogger()
    before = len(root.handlers)
    enable_transport("custom")
    assert disable_transport("custom") is True
    assert disable_transport("custom") is False  # idempotent
    assert len(root.handlers) == before
    assert closed.get("yes") is True


def test_factory_returning_none_is_soft_noop() -> None:
    register_transport("custom", lambda: None)
    assert enable_transport("custom") is False
    assert list_transports()["custom"]["enabled"] is False


def test_enable_unregistered_raises() -> None:
    with pytest.raises(ValueError):
        enable_transport("nope")


def test_list_transports_reports_state() -> None:
    snap = list_transports()
    assert snap["console"] == {"registered": True, "enabled": False}
    enable_transport("console")
    assert list_transports()["console"]["enabled"] is True


def test_reconcile_after_external_handler_removal() -> None:
    register_transport("custom", lambda: logging.NullHandler())
    enable_transport("custom")
    handler = transports._active["custom"]
    # Simulate configure_logging()'s basicConfig(force=True) wiping handlers.
    logging.getLogger().removeHandler(handler)
    # list_transports reconciles -> custom no longer enabled.
    assert list_transports()["custom"]["enabled"] is False
    # Re-enabling re-adds cleanly (no stale _active entry blocking it).
    assert enable_transport("custom") is True
