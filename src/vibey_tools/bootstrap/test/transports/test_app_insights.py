"""App Insights transport: delegation, unavailable no-op, detach-on-disable."""

from __future__ import annotations

import logging

from vibey_bootstrap.transports import builtins as tb
from vibey_bootstrap.transports import disable_transport, enable_transport, list_transports


def test_unavailable_telemetry_is_soft_noop(monkeypatch) -> None:
    monkeypatch.setattr(
        "vibey_bootstrap.services.telemetry.TELEMETRY_AVAILABLE", False, raising=False
    )
    assert enable_transport("app_insights") is False
    assert list_transports()["app_insights"]["enabled"] is False


def test_delegates_to_telemetry_and_registry_owns_handler(monkeypatch) -> None:
    sentinel = logging.NullHandler()

    def fake_factory() -> logging.Handler:
        return sentinel

    # Replace the factory so we don't need a real Azure Monitor exporter.
    monkeypatch.setattr(tb, "make_app_insights_handler", fake_factory)
    from vibey_bootstrap.transports import register_transport

    register_transport("app_insights", fake_factory, replace=True)

    root = logging.getLogger()
    assert enable_transport("app_insights") is True
    assert sentinel in root.handlers
    # disable detaches the handler from root (suppress semantics).
    assert disable_transport("app_insights") is True
    assert sentinel not in root.handlers


def test_make_handler_delegates_to_configure(monkeypatch) -> None:
    import vibey_bootstrap.services.telemetry as telemetry

    monkeypatch.setattr(telemetry, "TELEMETRY_AVAILABLE", True, raising=False)
    called: dict[str, object] = {}
    added = logging.NullHandler()

    def fake_configure(*a, **k):  # noqa: ANN002, ANN003
        called["configured"] = True
        logging.getLogger().addHandler(added)
        return True

    monkeypatch.setattr(telemetry.telemetry_manager, "configure", fake_configure)

    handler = tb.make_app_insights_handler()
    # The factory pulls the handler back off root so the registry owns it.
    assert called.get("configured") is True
    assert handler is added
    assert added not in logging.getLogger().handlers
