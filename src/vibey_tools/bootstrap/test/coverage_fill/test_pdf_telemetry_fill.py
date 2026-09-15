"""PDF action stripping and the App Insights telemetry manager.

Both modules exist to be optional: the PDF scrubber must pass a malformed document
through untouched rather than fail a report, and the telemetry manager must fall back to
plain logging whenever Azure Monitor is absent or misconfigured.
"""

from __future__ import annotations

import importlib
import logging
import sys
from unittest.mock import MagicMock, patch

import pytest

from vibey_bootstrap import pdf_safety
from vibey_bootstrap.counters import _reset_counters, counter_snapshot
from vibey_bootstrap.pdf_safety import _strip_keys, sanitize_pdf_for_passthrough
from vibey_bootstrap.services import telemetry as telemetry_mod
from vibey_bootstrap.services.telemetry import TelemetryManager

# ═══════════════════════════════════════════════════════════ pdf_safety


class Hostile(dict):
    """A PDF dictionary that raises on the key nobody should be able to delete."""

    def __contains__(self, key) -> bool:
        if key == "/AA":
            raise RuntimeError("indirect object is unresolvable")
        return super().__contains__(key)


def reader(root=None, pages=()) -> MagicMock:
    r = MagicMock()
    r.trailer = {"/Root": root if root is not None else {}}
    r.pages = list(pages)
    return r


def test_stripping_nothing_removes_nothing():
    assert _strip_keys(None, ("/A",)) == 0


def test_a_key_that_cannot_be_read_is_skipped_and_the_rest_still_go():
    obj = Hostile({"/A": 1, "/AA": 2})
    assert _strip_keys(obj, ("/A", "/AA")) == 1
    assert "/A" not in obj


def test_acroform_field_actions_are_stripped():
    _reset_counters()
    field = {"/A": "javascript:evil", "/AA": {}}
    root = {"/AcroForm": {"/Fields": [field]}}
    sanitize_pdf_for_passthrough(reader(root=root))
    assert field == {}
    assert counter_snapshot()["pdf.sanitized.actions_stripped"] == 1


def test_a_field_that_cannot_be_scrubbed_does_not_stop_the_others():
    good = {"/A": 1}
    root = {"/AcroForm": {"/Fields": [Hostile({"/AA": 1}), good]}}
    sanitize_pdf_for_passthrough(reader(root=root))
    assert good == {}


def test_annotation_actions_are_stripped_through_the_indirect_reference():
    target = {"/A": "https://evil.example.com", "/AA": {}}
    annot = MagicMock()
    annot.get_object.return_value = target
    page = {"/Annots": [annot]}
    sanitize_pdf_for_passthrough(reader(pages=[page]))
    assert target == {}


def test_an_annotation_that_cannot_be_resolved_is_scrubbed_directly():
    annot = MagicMock()
    annot.get_object.side_effect = RuntimeError("broken xref")
    annot.__contains__ = lambda self, key: False
    page = {"/Annots": [annot]}
    sanitize_pdf_for_passthrough(reader(pages=[page]))  # must not raise


def test_a_page_that_cannot_be_read_does_not_stop_the_next_one():
    class BadPage:
        def __contains__(self, key):
            raise RuntimeError("page object is corrupt")

    good = {"/AA": 1}
    sanitize_pdf_for_passthrough(reader(pages=[BadPage(), good]))
    assert good == {}


def test_a_scrub_that_fails_outright_passes_the_document_through(monkeypatch, caplog):
    monkeypatch.setattr(
        pdf_safety, "bump_counter", MagicMock(side_effect=RuntimeError("counters are down"))
    )
    r = reader(root={"/OpenAction": 1})
    with caplog.at_level(logging.ERROR):
        assert sanitize_pdf_for_passthrough(r) is r
    assert "passing through" in caplog.text


# ═══════════════════════════════════════════════════════════ telemetry


@pytest.fixture
def manager():
    return TelemetryManager()


def test_configuring_twice_is_a_no_op_unless_reconfiguration_is_asked_for(manager):
    manager._configured = True
    assert manager.configure() is True


def test_without_a_connection_string_it_falls_back_to_basic_logging(manager, monkeypatch):
    monkeypatch.delenv("APPLICATIONINSIGHTS_CONNECTION_STRING", raising=False)
    assert manager.configure() is True
    assert manager.tracer is None


def test_without_the_azure_monitor_extra_it_falls_back_to_basic_logging(manager, monkeypatch):
    monkeypatch.setattr(telemetry_mod, "TELEMETRY_AVAILABLE", False)
    assert manager.configure(connection_string="InstrumentationKey=k") is True
    assert manager.tracer is None


def test_a_full_configuration_instruments_functions_and_gets_a_tracer(manager, monkeypatch):
    monkeypatch.setattr(telemetry_mod, "TELEMETRY_AVAILABLE", True)
    configure = MagicMock()
    monkeypatch.setattr(telemetry_mod, "configure_azure_monitor", configure, raising=False)
    instrumentor = MagicMock()
    monkeypatch.setattr(telemetry_mod, "AZURE_FUNCTIONS_INSTRUMENTOR_AVAILABLE", True)
    monkeypatch.setattr(telemetry_mod, "AzureFunctionsInstrumentor", instrumentor, raising=False)
    trace = MagicMock()
    monkeypatch.setattr(telemetry_mod, "trace", trace, raising=False)

    assert manager.configure(connection_string="InstrumentationKey=k") is True
    configure.assert_called_once()
    instrumentor.return_value.instrument.assert_called_once()
    assert manager.tracer is trace.get_tracer.return_value


def test_a_configuration_failure_still_leaves_logging_working(manager, monkeypatch):
    monkeypatch.setattr(telemetry_mod, "TELEMETRY_AVAILABLE", True)
    monkeypatch.setattr(
        telemetry_mod,
        "configure_azure_monitor",
        MagicMock(side_effect=RuntimeError("bad connection string")),
        raising=False,
    )
    assert manager.configure(connection_string="InstrumentationKey=k") is True
    assert manager._configured is True


def test_a_successful_upgrade_from_config_is_reported(manager, monkeypatch):
    monkeypatch.delenv("APPLICATIONINSIGHTS_CONNECTION_STRING", raising=False)
    repo = MagicMock()
    repo.get_secret_value.return_value = "InstrumentationKey=k"
    monkeypatch.setattr(
        manager,
        "configure",
        MagicMock(side_effect=lambda **kw: setattr(manager, "tracer", object()) or True),
    )
    assert manager.try_upgrade_from_config(repo) is True


def test_the_transition_message_names_app_insights_once_a_tracer_exists(
    manager, monkeypatch, caplog
):
    from vibey_bootstrap.services.bootstrap_logging import BootstrapLogger

    monkeypatch.setattr(BootstrapLogger, "is_bootstrap_configured", staticmethod(lambda: True))
    manager.tracer = MagicMock()
    with caplog.at_level(logging.INFO):
        manager._configure_logging()
    assert "with App Insights" in caplog.text


def test_a_span_is_created_only_when_telemetry_is_really_available(manager, monkeypatch):
    monkeypatch.setattr(telemetry_mod, "TELEMETRY_AVAILABLE", True)
    manager.tracer = MagicMock()
    span = manager.create_span("op", {"k": "v"})
    assert span is manager.tracer.start_span.return_value
    manager.tracer.start_span.assert_called_once_with("op", attributes={"k": "v"})


def test_the_module_degrades_when_azure_monitor_is_not_installed(caplog):
    """Reimport the module with the optional imports made to fail."""
    real_import = (
        __builtins__["__import__"] if isinstance(__builtins__, dict) else __builtins__.__import__
    )

    def refuse(name, *a, **kw):
        if name.startswith("azure.monitor") or name.startswith("opentelemetry"):
            raise ImportError(f"no {name}")
        return real_import(name, *a, **kw)

    saved = sys.modules.pop("vibey_bootstrap.services.telemetry")
    try:
        with patch("builtins.__import__", refuse), caplog.at_level(logging.WARNING):
            degraded = importlib.import_module("vibey_bootstrap.services.telemetry")
        assert degraded.TELEMETRY_AVAILABLE is False
        assert degraded.AZURE_FUNCTIONS_INSTRUMENTOR_AVAILABLE is False
        assert "not available" in caplog.text
    finally:
        sys.modules["vibey_bootstrap.services.telemetry"] = saved


def test_the_module_uses_the_functions_instrumentor_when_it_is_installed():
    """The instrumentor is not published standalone, so stand one in and reimport."""
    instrumentor = MagicMock()
    stub = type(sys)("opentelemetry.instrumentation.azure_functions")
    stub.AzureFunctionsInstrumentor = instrumentor

    saved = sys.modules.pop("vibey_bootstrap.services.telemetry")
    try:
        with patch.dict(sys.modules, {"opentelemetry.instrumentation.azure_functions": stub}):
            reimported = importlib.import_module("vibey_bootstrap.services.telemetry")
            assert reimported.AZURE_FUNCTIONS_INSTRUMENTOR_AVAILABLE is True
            assert reimported.AzureFunctionsInstrumentor is instrumentor
    finally:
        sys.modules["vibey_bootstrap.services.telemetry"] = saved
