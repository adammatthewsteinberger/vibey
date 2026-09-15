"""Broad v3 integration-style unit tests for coverage."""

from __future__ import annotations

import logging
import sys
from unittest.mock import MagicMock, patch

import pytest

from vibey_bootstrap.http import build_session
from vibey_bootstrap.transports.adx import AdxHandler
from vibey_bootstrap.transports.blob import BlobHandler
from vibey_bootstrap.transports.nosql import NoSqlHandler


def test_build_session_returns_requests_session() -> None:
    session = build_session()
    assert hasattr(session, "post")


def test_blob_block_mode() -> None:
    container = MagicMock()
    blob = MagicMock()
    container.get_blob_client.return_value = blob
    h = BlobHandler(container_client=container, mode="block", flush_interval=3600.0)
    try:
        rec = logging.LogRecord("s", logging.INFO, __file__, 1, "line", None, None)
        h.emit(rec)
        h.flush()
    finally:
        h.close()
    blob.upload_blob.assert_called_once()


def test_nosql_with_ttl_index() -> None:
    pytest.importorskip("pymongo")
    collection = MagicMock()
    client = MagicMock()
    with patch("vibey_bootstrap.transports.nosql._connect", return_value=(client, collection)):
        h = NoSqlHandler(
            uri="mongodb://localhost",
            database="db",
            ttl_seconds=3600,
            flush_interval=3600.0,
            batch_size=1,
        )
        try:
            h.emit(logging.LogRecord("s", logging.INFO, __file__, 1, "m", None, None))
            h.flush()
        finally:
            h.close()
    collection.create_index.assert_called()


def test_adx_ingest_stream() -> None:
    h = AdxHandler(cluster_uri="https://cluster", database="db", flush_interval=3600.0)
    client = MagicMock()
    fake_data_format = MagicMock()
    fake_props = MagicMock()
    fake_kusto_data = MagicMock()
    fake_kusto_data.data_format.DataFormat = fake_data_format
    fake_kusto_ingest = MagicMock()
    fake_kusto_ingest.IngestionProperties = fake_props
    with patch.object(h, "_get_client", return_value=client):
        with patch.dict(
            sys.modules,
            {
                "azure.kusto.data": MagicMock(),
                "azure.kusto.data.data_format": fake_kusto_data.data_format,
                "azure.kusto.ingest": fake_kusto_ingest,
            },
        ):
            h.setFormatter(logging.Formatter("%(message)s"))
            h.emit(logging.LogRecord("s", logging.INFO, __file__, 1, '{"a":1}', None, None))
            h.flush()
    client.ingest_from_stream.assert_called()
    h.close()
