"""Parametrized transport contract tests — same guarantees as Sumo for every sink."""

from __future__ import annotations

import gzip
import json
import logging
from test.v3.conftest import PostRecorder, log_record, patch_session_post
from unittest.mock import MagicMock, patch

import pytest

from vibey_bootstrap.counters import counter_snapshot
from vibey_bootstrap.transports._base import ShipResult, _BufferedShipper
from vibey_bootstrap.transports.adx import AdxHandler
from vibey_bootstrap.transports.blob import BlobHandler
from vibey_bootstrap.transports.event_hubs import EventHubsHandler
from vibey_bootstrap.transports.nosql import NoSqlHandler
from vibey_bootstrap.transports.panther import PantherHandler
from vibey_bootstrap.transports.sql import SqlHandler
from vibey_bootstrap.transports.sumologic import SumoLogicHandler

# ---------------------------------------------------------------------------
# HTTP-based handlers (Sumo + Panther)
# ---------------------------------------------------------------------------


@pytest.fixture(params=["sumo", "panther"])
def http_handler(request) -> tuple[logging.Handler, PostRecorder, str]:
    if request.param == "sumo":
        h = SumoLogicHandler(
            endpoint_url="https://example.test/r",
            flush_interval=3600.0,
            batch_size=1000,
        )
        prefix = "sumologic"
    else:
        h = PantherHandler(
            api_host="https://panther.test",
            log_source_id="src",
            log_source_token="tok",
            flush_interval=3600.0,
            batch_size=1000,
        )
        prefix = "panther"
    rec = PostRecorder()
    patch_session_post(h, rec)
    yield h, rec, prefix
    h.close()


def test_http_emit_buffers_without_post(http_handler) -> None:
    h, rec, _ = http_handler
    h.emit(log_record())
    assert rec.calls == []


def test_http_flush_never_raises_on_network_error(http_handler) -> None:
    h, rec, prefix = http_handler
    rec.raise_exc = ConnectionError("down")
    before = counter_snapshot().get(f"{prefix}.transport.error", 0)
    h.emit(log_record())
    h.flush()
    assert counter_snapshot().get(f"{prefix}.transport.error", 0) >= before + 1


def test_http_429_bumps_throttled(http_handler) -> None:
    h, rec, prefix = http_handler
    rec.status_code = 429
    before_thr = counter_snapshot().get(f"{prefix}.transport.throttled", 0)
    h.emit(log_record())
    h.flush()
    if prefix == "panther":
        assert counter_snapshot().get(f"{prefix}.transport.throttled", 0) == before_thr + 1


def test_http_close_idempotent(http_handler) -> None:
    h, rec, _ = http_handler
    h.emit(log_record())
    h.close()
    h.close()


def test_http_overflow_drops(http_handler) -> None:
    h, rec, prefix = http_handler
    h.close()
    if prefix == "sumologic":
        h = SumoLogicHandler(
            endpoint_url="https://example.test/r",
            flush_interval=3600.0,
            batch_size=1000,
            max_buffer=2,
        )
    else:
        h = PantherHandler(
            api_host="https://panther.test",
            log_source_id="src",
            log_source_token="tok",
            flush_interval=3600.0,
            batch_size=1000,
            max_buffer=2,
        )
    patch_session_post(h, PostRecorder())
    try:
        for _ in range(5):
            h.emit(log_record())
        h.close()
        assert counter_snapshot().get(f"{prefix}.transport.dropped", 0) >= 1
    finally:
        if h._closed is False:  # type: ignore[attr-defined]
            h.close()


def test_panther_injects_correlation_id(monkeypatch) -> None:
    monkeypatch.setenv("CORRELATION_ID", "corr-123")
    from vibey_bootstrap.logging.correlation import set_correlation_id

    set_correlation_id("corr-123")
    h = PantherHandler(
        api_host="https://p.test",
        log_source_id="1",
        log_source_token="tok",
        flush_interval=3600.0,
    )
    rec = PostRecorder()
    patch_session_post(h, rec)
    try:
        h.emit(log_record("evt"))
        h.flush()
        body = json.loads(rec.calls[0]["data"].decode())
        assert body["events"][0].get("p_correlation_id") == "corr-123"
    finally:
        h.close()


def test_sumo_gzip_above_threshold() -> None:
    h = SumoLogicHandler(
        endpoint_url="https://example.test/r",
        gzip_threshold=10,
        flush_interval=3600.0,
    )
    rec = PostRecorder()
    patch_session_post(h, rec)
    try:
        h.emit(log_record("x" * 200))
        h.flush()
        assert rec.calls[0]["headers"].get("Content-Encoding") == "gzip"
        gzip.decompress(rec.calls[0]["data"])
    finally:
        h.close()


# ---------------------------------------------------------------------------
# Blob handler
# ---------------------------------------------------------------------------


def test_blob_append_and_block_modes() -> None:
    container = MagicMock()
    blob = MagicMock()
    container.get_blob_client.return_value = blob

    append = BlobHandler(container_client=container, mode="append", flush_interval=3600.0)
    try:
        append.emit(log_record("a"))
        append.flush()
    finally:
        append.close()
    blob.append_block.assert_called()

    blob.reset_mock()
    block = BlobHandler(container_client=container, mode="block", flush_interval=3600.0)
    try:
        block.emit(log_record("b"))
        block.flush()
    finally:
        block.close()
    blob.upload_blob.assert_called()


def test_blob_ship_failure_bumps_error() -> None:
    container = MagicMock()
    blob = MagicMock()
    blob.append_block.side_effect = RuntimeError("storage down")
    container.get_blob_client.return_value = blob
    h = BlobHandler(container_client=container, flush_interval=3600.0)
    before = counter_snapshot().get("blob.transport.error", 0)
    try:
        h.emit(log_record())
        h.flush()
    finally:
        h.close()
    assert counter_snapshot().get("blob.transport.error", 0) >= before + 1


# ---------------------------------------------------------------------------
# SQL handler (requires sqlalchemy)
# ---------------------------------------------------------------------------


@pytest.fixture
def sql_handler():
    pytest.importorskip("sqlalchemy")
    h = SqlHandler(dsn="sqlite:///:memory:", flush_interval=3600.0, batch_size=1000)
    yield h
    h.close()


def test_sql_ship_failure_bumps_error(sql_handler) -> None:
    before = counter_snapshot().get("sql.transport.error", 0)
    with patch.object(
        sql_handler,
        "_ship",
        return_value=__import__(
            "vibey_bootstrap.transports._base", fromlist=["ShipResult"]
        ).ShipResult(ok=False, count=0),
    ):
        sql_handler.emit(log_record())
        sql_handler.flush()
    assert counter_snapshot().get("sql.transport.error", 0) >= before + 1


def test_sql_ensure_table(sql_handler) -> None:
    sql_handler.ensure_table()


# ---------------------------------------------------------------------------
# NoSQL handler
# ---------------------------------------------------------------------------


@pytest.fixture
def nosql_handler():
    pytest.importorskip("pymongo")
    collection = MagicMock()
    client = MagicMock()
    with patch("vibey_bootstrap.transports.nosql._connect", return_value=(client, collection)):
        h = NoSqlHandler(
            uri="mongodb://localhost",
            database="db",
            ttl_seconds=60,
            flush_interval=3600.0,
            batch_size=1,
        )
        yield h, collection, client
        h.close()


def test_nosql_insert_many_on_flush(nosql_handler) -> None:
    h, collection, _ = nosql_handler
    h.emit(log_record("doc"))
    h.flush()
    collection.insert_many.assert_called()
    collection.create_index.assert_called()


def test_nosql_ship_failure_bumps_error(nosql_handler) -> None:
    h, collection, _ = nosql_handler
    collection.insert_many.side_effect = RuntimeError("mongo down")
    before = counter_snapshot().get("nosql.transport.error", 0)
    h.emit(log_record())
    h.flush()
    assert counter_snapshot().get("nosql.transport.error", 0) >= before + 1


# ---------------------------------------------------------------------------
# ADX + Event Hubs
# ---------------------------------------------------------------------------


def test_adx_ship_success() -> None:
    import sys

    h = AdxHandler(cluster_uri="https://c", database="db", flush_interval=3600.0)
    client = MagicMock()
    fake_data_format = MagicMock()
    fake_data_format.DataFormat = MagicMock(MULTIJSON="MULTIJSON")
    fake_kusto_ingest = MagicMock()
    with patch.object(h, "_get_client", return_value=client):
        with patch.dict(
            sys.modules,
            {
                "azure.kusto.data.data_format": fake_data_format,
                "azure.kusto.ingest": fake_kusto_ingest,
            },
        ):
            result = h._ship(['{"k":1}'])
    assert result.ok is True
    client.ingest_from_stream.assert_called()
    h.close()


def test_event_hubs_full_ship_path() -> None:
    import sys

    pytest.importorskip("azure.eventhub")
    h = EventHubsHandler(
        fully_qualified_namespace="ns.servicebus.windows.net",
        eventhub_name="logs",
        flush_interval=3600.0,
    )
    producer = MagicMock()
    batch = MagicMock()
    producer.create_batch.return_value = batch
    fake_eventhub = MagicMock()
    fake_eventhub.EventData = MagicMock(side_effect=lambda b: MagicMock(body=b))
    with patch.object(h, "_get_producer", return_value=producer):
        with patch.dict(sys.modules, {"azure.eventhub": fake_eventhub}):
            h.setFormatter(logging.Formatter("%(message)s"))
            h.emit(log_record("line"))
            h.flush()
    producer.send_batch.assert_called()
    h.close()


def test_event_hubs_ship_failure() -> None:
    h = EventHubsHandler(
        fully_qualified_namespace="ns.servicebus.windows.net",
        eventhub_name="logs",
        flush_interval=3600.0,
    )
    with patch.object(h, "_get_producer", side_effect=RuntimeError("eh down")):
        assert h._ship(['{"x":1}']).ok is False
    h.close()


def test_event_hubs_empty_batch() -> None:
    h = EventHubsHandler(
        fully_qualified_namespace="ns.servicebus.windows.net",
        eventhub_name="logs",
        flush_interval=3600.0,
    )
    assert h._ship([]).ok is True
    h.close()


def test_buffered_shipper_ship_exception_bumps_error() -> None:
    class _Boom(_BufferedShipper):
        def _ship(self, batch: list[str]) -> ShipResult:
            raise RuntimeError("boom")

    h = _Boom(counter_prefix="boomship", flush_interval=3600.0)
    before = counter_snapshot().get("boomship.transport.error", 0)
    try:
        h.emit(log_record())
        h.flush()
    finally:
        h.close()
    assert counter_snapshot().get("boomship.transport.error", 0) >= before + 1
