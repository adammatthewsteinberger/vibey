"""The closing set: bootstrap logging, DB helpers, the outbox, and rendering variants.

Nothing exotic left — these are the last untaken branches, mostly "the optional path"
and "the failure path" of helpers that already have their happy path covered.
"""

from __future__ import annotations

import asyncio
import json
import logging
from unittest.mock import MagicMock, patch

import pytest

from vibey_bootstrap import db as db_mod
from vibey_bootstrap.counters import _reset_counters, counter_snapshot
from vibey_bootstrap.db import outbox as outbox_mod
from vibey_bootstrap.logging import correlation
from vibey_bootstrap.notify import templates
from vibey_bootstrap.services import bootstrap_logging
from vibey_bootstrap.services.bootstrap_logging import BootstrapLogger, ExtraFieldsFormatter


@pytest.fixture(autouse=True)
def counters():
    _reset_counters()


# ═══════════════════════════════════════════════════ bootstrap logging


def test_extra_fields_that_will_not_serialise_are_still_rendered():
    record = logging.LogRecord("svc", logging.INFO, __file__, 1, "hello", None, None)
    record.tenant = "acme"  # type: ignore[attr-defined]
    formatter = ExtraFieldsFormatter("%(message)s")
    with patch.object(bootstrap_logging.json, "dumps", side_effect=TypeError("not encodable")):
        rendered = formatter.format(record)
    assert rendered.startswith("hello | ")
    assert "acme" in rendered


def test_bootstrap_logging_installs_a_handler_when_root_has_none(monkeypatch):
    # configure_bootstrap_logging() is idempotent, so an earlier test in the session
    # would otherwise make this a no-op.
    monkeypatch.setattr(BootstrapLogger, "_configured", False)
    root = logging.getLogger()
    saved = list(root.handlers)
    root.handlers.clear()
    try:
        BootstrapLogger.configure_bootstrap_logging()
        assert root.handlers
        assert isinstance(root.handlers[0].formatter, ExtraFieldsFormatter)
    finally:
        root.handlers[:] = saved


def test_the_convenience_wrapper_configures_bootstrap_logging():
    with patch.object(BootstrapLogger, "configure_bootstrap_logging") as configure:
        bootstrap_logging.ensure_bootstrap_logging()
    configure.assert_called_once()


def test_the_module_self_configures_inside_an_azure_functions_worker(monkeypatch):
    """Under the Functions worker the module configures logging on import, so a host
    that logs before the app calls anything still gets formatted records."""
    import importlib
    import sys

    monkeypatch.setenv("FUNCTIONS_WORKER_RUNTIME", "python")
    saved_module = sys.modules.pop("vibey_bootstrap.services.bootstrap_logging")
    root = logging.getLogger()
    saved_handlers = list(root.handlers)
    try:
        reimported = importlib.import_module("vibey_bootstrap.services.bootstrap_logging")
        # A fresh class object, so its flag reflects only this import.
        assert reimported.BootstrapLogger.is_bootstrap_configured() is True
    finally:
        root.handlers[:] = saved_handlers
        sys.modules["vibey_bootstrap.services.bootstrap_logging"] = saved_module


# ═══════════════════════════════════════════════════ application bootstrap


def test_a_bootstrap_whose_phases_all_pass_but_leave_no_repository_is_an_error(monkeypatch):
    from vibey_bootstrap.services.application_bootstrap import ApplicationBootstrap

    boot = ApplicationBootstrap()
    for phase in (
        "_initialize_telemetry_from_environment",
        "_load_enhanced_configuration",
        "_upgrade_telemetry_from_config",
        "_finalize_configuration_loading",
    ):
        monkeypatch.setattr(boot, phase, MagicMock())
    boot.config_repository = None

    with pytest.raises(RuntimeError, match="config repository is None"):
        boot.initialize()


def test_the_telemetry_upgrade_is_skipped_without_a_repository(caplog):
    from vibey_bootstrap.services.application_bootstrap import ApplicationBootstrap

    boot = ApplicationBootstrap()
    boot.config_repository = None
    with caplog.at_level(logging.WARNING):
        boot._upgrade_telemetry_from_config()
    assert "skipping telemetry upgrade" in caplog.text


# ═══════════════════════════════════════════════════ correlation filter


def test_the_correlation_filter_survives_a_record_it_cannot_inspect():
    class Hostile:
        @property
        def __dict__(self):
            raise RuntimeError("record internals are unreadable")

    with correlation.correlation_scope("cid"):
        assert correlation.CorrelationFilter().filter(Hostile()) is True


# ═══════════════════════════════════════════════════════════════ db


def test_a_server_dsn_gets_a_bounded_pool(monkeypatch):
    import sqlalchemy

    monkeypatch.setenv("DATABASE_URL", "postgresql://host/db")
    created = MagicMock()
    monkeypatch.setattr(sqlalchemy, "create_engine", created)
    db_mod.create_engine_from_env()
    assert created.call_args.kwargs["pool_size"] == 5
    assert created.call_args.kwargs["max_overflow"] == 10


def test_db_health_reports_a_database_it_cannot_reach(monkeypatch):
    monkeypatch.setattr(
        db_mod, "get_engine", MagicMock(side_effect=RuntimeError("connection refused"))
    )
    result = db_mod.db_health()
    assert result["status"] == "error"
    assert result["latency_ms"] is None
    assert "connection refused" in result["error"]


def test_the_db_reset_is_test_only(monkeypatch):
    monkeypatch.delenv("AZURE_BOOTSTRAP_ALLOW_RESET", raising=False)
    with pytest.raises(RuntimeError, match="test-only"):
        db_mod._reset_db()


def test_resetting_the_db_survives_an_engine_that_will_not_dispose(monkeypatch):
    engine = MagicMock()
    engine.dispose.side_effect = RuntimeError("pool already gone")
    monkeypatch.setattr(db_mod, "_engine", engine)
    db_mod._reset_db()
    assert db_mod._engine is None


# ═══════════════════════════════════════════════════════════ outbox


def test_an_outbox_table_name_that_is_not_an_identifier_is_refused():
    with pytest.raises(ValueError, match="Invalid SQL identifier"):
        outbox_mod._validate_identifier("outbox; DROP TABLE users")


def test_a_send_that_fails_marks_the_row_failed_and_drains_on(caplog):
    session = MagicMock()
    session.execute.return_value.fetchall.return_value = [
        ("id-1", json.dumps({"n": 1})),
        ("id-2", {"n": 2}),
    ]

    with patch.object(outbox_mod, "Outbox") as outbox_cls:
        outbox = outbox_cls.return_value
        outbox.claim.return_value = True
        sender = MagicMock(side_effect=[RuntimeError("broker refused"), None])
        with caplog.at_level(logging.WARNING):
            assert outbox_mod.drain_outbox(session, sender) == 1

    outbox.mark_failed.assert_called_once()
    assert outbox.mark_failed.call_args.args[0] == "id-1"
    assert "outbox drain failed for id-1" in caplog.text


# ═══════════════════════════════════════════════════════ async consumer


async def test_a_message_received_after_the_stop_signal_is_abandoned_not_processed():
    """Shutdown mid-batch: the remaining messages go back to the broker untouched."""
    from vibey_bootstrap.servicebus.async_ext import run_async_consumer

    stop = asyncio.Event()
    first, second = object(), object()
    handled: list[object] = []
    abandoned: list[object] = []
    completed: list[object] = []

    receiver = MagicMock()
    receiver.__aenter__ = _async(receiver)
    receiver.__aexit__ = _async(False)

    async def receive_messages(max_wait_time):
        return [first, second]

    async def abandon(msg):
        abandoned.append(msg)

    async def complete(msg):
        completed.append(msg)

    async def handler(msg):
        handled.append(msg)
        stop.set()  # shut down while the batch is still being drained

    receiver.receive_messages = receive_messages
    receiver.abandon_message = abandon
    receiver.complete_message = complete
    client = MagicMock()
    client.get_queue_receiver.return_value = receiver

    await run_async_consumer(client, "q", handler, stop_event=stop)

    assert handled == [first] and completed == [first]
    assert abandoned == [second]


async def test_a_handler_that_raises_abandons_rather_than_completes():
    from vibey_bootstrap.servicebus.async_ext import run_async_consumer

    stop = asyncio.Event()
    message = object()
    receiver = MagicMock()
    receiver.__aenter__ = _async(receiver)
    receiver.__aexit__ = _async(False)

    async def receive_messages(max_wait_time):
        stop_after.append(1)
        return [message] if len(stop_after) == 1 else []

    stop_after: list[int] = []
    abandoned: list[object] = []

    async def abandon(msg):
        abandoned.append(msg)
        stop.set()

    receiver.receive_messages = receive_messages
    receiver.abandon_message = abandon
    receiver.complete_message = lambda msg: _completed(None)

    async def handler(msg):
        raise RuntimeError("handler exploded")

    client = MagicMock()
    client.get_queue_receiver.return_value = receiver

    await run_async_consumer(client, "q", handler, stop_event=stop)
    assert abandoned == [message]


def _async(value):
    async def _call(*a, **kw):
        return value

    return _call


def _completed(value):
    future: asyncio.Future = asyncio.get_event_loop().create_future()
    future.set_result(value)
    return future


# ═══════════════════════════════════════════════════════════ email


def test_the_acs_client_is_built_once_on_first_send(monkeypatch):
    from vibey_bootstrap.email import AcsEmailSender

    monkeypatch.setenv("ACS_CONNECTION_STRING", "endpoint=https://acs;accesskey=k")
    monkeypatch.setenv("ACS_SENDER_ADDRESS", "noreply@example.com")
    sender = AcsEmailSender()

    client = MagicMock()
    client.begin_send.return_value.result.return_value = MagicMock(id="msg-1")
    with patch(
        "azure.communication.email.EmailClient.from_connection_string", return_value=client
    ) as factory:
        assert sender.send(to=["a@example.com"], subject="s", html_body="<p>h</p>") == "msg-1"
        assert sender._get_client() is client
    factory.assert_called_once()


# ═══════════════════════════════════════════════════════════ ingress


def test_an_extension_allowlist_ignores_blank_entries():
    from vibey_bootstrap.ingress.extensions import ExtensionAllowlist

    allowlist = ExtensionAllowlist([".pdf", "", "PNG"])
    assert allowlist.allowed == frozenset({".pdf", ".png"})
    assert allowlist.allows("scan.PNG") is True
    assert allowlist._suffix("") == ""


def test_a_mime_allowlist_reports_its_set_and_rejects_a_missing_type():
    from vibey_bootstrap.ingress.mime import MimeAllowlist

    allowlist = MimeAllowlist(["application/pdf"])
    assert allowlist.allowed == frozenset({"application/pdf"})
    assert allowlist.allows(None) is False


def test_a_rejected_classification_never_matches_an_extension():
    from vibey_bootstrap.ingress.magic_bytes import extension_matches_kind

    assert extension_matches_kind("doc.pdf", "reject") is False
    assert extension_matches_kind("", "pdf") is False


@pytest.mark.parametrize(
    "kwargs, counter",
    [
        ({"max_entries": 1}, "zip.too_many_entries"),
        ({"max_uncompressed_bytes": 1}, "zip.too_large"),
    ],
)
def test_zip_bomb_limits_bump_the_counter_they_were_given(kwargs, counter):
    from vibey_bootstrap.ingress.zip_safety import ZipBombError, enforce_zip_safety_limits

    archive = MagicMock()
    archive.infolist.return_value = [MagicMock(file_size=1000), MagicMock(file_size=1000)]
    with pytest.raises(ZipBombError):
        enforce_zip_safety_limits(archive, filename="a.zip", counter_name=counter, **kwargs)
    assert counter_snapshot()[counter] == 1


def test_the_sender_notification_throttle_reset_is_test_only(monkeypatch):
    from vibey_bootstrap.notify.throttle import reset_sender_notification_throttle

    monkeypatch.delenv("AZURE_BOOTSTRAP_ALLOW_RESET", raising=False)
    with pytest.raises(RuntimeError, match="test-only"):
        reset_sender_notification_throttle()


# ═══════════════════════════════════════════════════════════ templates


def test_an_empty_table_renders_as_nothing():
    assert templates._table([]) == ""


def test_the_dev_validation_notice_carries_the_triage_context():
    body = templates.build_validation_notice_body(
        attachment_name="scan.pdf",
        correlation_id="cid-1",
        sender="a@example.com",
        issues=[],
        audience="dev",
        product_name="report",
        sender_send_failed=True,
        queue="ingest",
    )
    assert "Sender-facing notice ALSO failed" in body
    assert "queue" in body and "ingest" in body


def test_the_dev_unprocessable_notice_includes_the_email_identifiers():
    from vibey_bootstrap.notify.templates import UnprocessableReason

    _, _, _, dev_body = templates.build_unprocessable_notification(
        failure_reason=list(UnprocessableReason)[0],
        sender="a@example.com",
        attachment_summary=[
            {
                "name": "scan.pdf",
                "size": 10,
                "mime": "application/pdf",
                "classification": "pdf",
                "reject_reason": "",
            }
        ],
        correlation_id="cid-1",
        email_subject="Monthly report",
        email_id="msg-42",
    )
    assert "Monthly report" in dev_body
    assert "msg-42" in dev_body


# ═══════════════════════════════════════════════════════════ health


def test_an_azure_handler_on_a_named_logger_is_found_too(monkeypatch):
    from vibey_bootstrap import health as health_mod

    monkeypatch.setenv("USE_MOCK_BOOTSTRAP", "0")
    monkeypatch.setenv("APPLICATIONINSIGHTS_CONNECTION_STRING", "InstrumentationKey=k")

    class AzureMonitorLogExporterHandler(logging.Handler):
        def emit(self, record): ...

    logger = logging.getLogger("vibey.test.telemetry")
    handler = AzureMonitorLogExporterHandler()
    logger.addHandler(handler)
    root = logging.getLogger()
    saved = list(root.handlers)
    root.handlers.clear()
    try:
        assert health_mod.check_app_insights_logging()["status"] == "ok"
    finally:
        logger.removeHandler(handler)
        root.handlers[:] = saved


# ═══════════════════════════════════════════════════════════ retry


def test_a_rate_limit_callback_that_raises_does_not_mask_the_original_error():
    from vibey_bootstrap.exceptions import RateLimitError
    from vibey_bootstrap.retry import build_retry

    decorate = build_retry(
        operation="ai.call",
        retry_on=RateLimitError,
        max_attempts=1,
        wait_min_seconds=0,
        wait_max_seconds=0,
        counter_namespace="ai",
        rate_limit_callback=MagicMock(side_effect=RuntimeError("hook broke")),
    )

    @decorate
    def call():
        raise RateLimitError("429")

    with pytest.raises(RateLimitError):
        call()
    assert counter_snapshot()["ai.calls.rate_limit_or_http_error"] == 1


def test_an_exhausted_retry_is_labelled_by_what_finally_failed():
    from vibey_bootstrap.exceptions import RateLimitError
    from vibey_bootstrap.retry import build_retry

    decorate = build_retry(
        operation="ai.call",
        retry_on=RateLimitError,
        max_attempts=2,
        wait_min_seconds=0,
        wait_max_seconds=0,
        counter_namespace="ai",
        reraise=False,
    )

    @decorate
    def call():
        raise RateLimitError("429")

    from tenacity import RetryError

    with pytest.raises(RetryError):
        call()
    assert counter_snapshot()["ai.calls.rate_limit_or_http_error"] == 1


# ═══════════════════════════════════════════════════ correlation filter


def test_the_correlation_filter_survives_a_broken_context_var(monkeypatch):
    class Exploding:
        def get(self):
            raise RuntimeError("context var is unreadable")

    monkeypatch.setitem(correlation._VARS, "correlation_id", Exploding())
    record = logging.LogRecord("svc", logging.INFO, __file__, 1, "m", None, None)
    assert correlation.CorrelationFilter().filter(record) is True


# ═══════════════════════════════════════════════════════════ pdf_safety


def test_a_scrubber_that_raises_on_one_field_still_does_the_others(monkeypatch):
    from vibey_bootstrap import pdf_safety

    bad, good = {"/A": 1}, {"/A": 2}
    real_strip = pdf_safety._strip_keys

    def strip(obj, keys):
        if obj is bad:
            raise RuntimeError("field object exploded")
        return real_strip(obj, keys)

    monkeypatch.setattr(pdf_safety, "_strip_keys", strip)
    reader = MagicMock()
    reader.trailer = {"/Root": {"/AcroForm": {"/Fields": [bad, good]}}}
    reader.pages = []
    pdf_safety.sanitize_pdf_for_passthrough(reader)
    assert good == {}


def test_a_scrubber_that_raises_on_one_annotation_still_does_the_others(monkeypatch):
    from vibey_bootstrap import pdf_safety

    bad, good = {"/A": 1}, {"/A": 2}
    real_strip = pdf_safety._strip_keys

    def strip(obj, keys):
        if obj is bad:
            raise RuntimeError("annotation object exploded")
        return real_strip(obj, keys)

    monkeypatch.setattr(pdf_safety, "_strip_keys", strip)
    reader = MagicMock()
    reader.trailer = {"/Root": {}}
    reader.pages = [{"/Annots": [bad, good]}]
    pdf_safety.sanitize_pdf_for_passthrough(reader)
    assert good == {}
