"""Additional transport and module coverage."""

from __future__ import annotations

import logging
import sys
from unittest.mock import MagicMock, patch

import pytest

from vibey_bootstrap.contrib.scaffold import main
from vibey_bootstrap.transports.adx import AdxHandler
from vibey_bootstrap.transports.event_hubs import EventHubsHandler
from vibey_bootstrap.transports.file import make_file_handler
from vibey_bootstrap.transports.panther import PantherSearchClient, make_panther_search_client


def test_file_handler_time_rotation(tmp_path, monkeypatch) -> None:
    log_path = tmp_path / "app.jsonl"
    monkeypatch.setenv("FILE_LOG_PATH", str(log_path))
    monkeypatch.setenv("FILE_LOG_ROTATION", "time")
    handler = make_file_handler()
    assert handler is not None
    handler.close()


def test_panther_search_client(monkeypatch) -> None:
    monkeypatch.setenv("PANTHER_API_HOST", "https://p.test")
    monkeypatch.setenv("PANTHER_API_KEY", "key")
    client = make_panther_search_client()
    assert isinstance(client, PantherSearchClient)
    with patch.object(client._session, "post") as post:
        post.return_value = MagicMock(
            status_code=200, json=lambda: {"data": {"search": {"events": []}}}
        )
        assert client.search("error") == []
    client.close()


def test_adx_ship_with_kusto_mock() -> None:
    h = AdxHandler(cluster_uri="https://c", database="db", flush_interval=3600.0)
    mock_client = MagicMock()
    with patch.object(h, "_get_client", return_value=mock_client):
        with patch("vibey_bootstrap.transports.adx.DataFormat", create=True):
            with patch("vibey_bootstrap.transports.adx.IngestionProperties", create=True):
                rec = logging.LogRecord("s", logging.INFO, __file__, 1, "m", None, None)
                h.setFormatter(logging.Formatter("%(message)s"))
                h.emit(rec)
                h.flush()
    h.close()


def test_event_hubs_ship_batch() -> None:
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
            result = h._ship(['{"msg":"x"}'])
    assert result.ok is True
    producer.send_batch.assert_called_once()
    batch.add.assert_called_once()
    h.close()


def test_scaffold_cli_list() -> None:
    assert main(["list"]) == 0
