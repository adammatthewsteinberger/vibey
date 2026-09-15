# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Panther, ADX and Event Hubs: lazy client construction and the failure paths.

The three cloud shippers all build their SDK client on first use rather than at
construction, so a missing credential or an unreachable endpoint costs a dropped batch
instead of a failed start-up. These tests pin that down without touching a network.
"""

from __future__ import annotations

import gzip
import json
import logging
from unittest.mock import MagicMock, patch

import pytest

from vibey_bootstrap.counters import _reset_counters, counter_snapshot
from vibey_bootstrap.transports import adx as adx_mod
from vibey_bootstrap.transports import event_hubs as eh_mod
from vibey_bootstrap.transports import panther as panther_mod
from vibey_bootstrap.transports.adx import AdxHandler, make_adx_handler
from vibey_bootstrap.transports.event_hubs import EventHubsHandler, make_event_hubs_handler
from vibey_bootstrap.transports.panther import (
    PantherHandler,
    PantherSearchClient,
    make_panther_search_client,
)


def record(msg: str = "hi") -> logging.LogRecord:
    return logging.LogRecord("svc", logging.INFO, __file__, 1, msg, None, None)


class Credential:
    """The duck type the Azure SDKs require; never actually asked for a token here."""

    def get_token(self, *scopes, **kw):  # pragma: no cover - no request is made
        raise AssertionError("no token is fetched in these tests")

    def close(self) -> None:  # pragma: no cover - not always called
        pass


# ═══════════════════════════════════════════════════════════════ Panther


@pytest.fixture
def panther():
    with patch.object(panther_mod, "_build_session", return_value=MagicMock()):
        h = PantherHandler(
            api_host="https://panther.example.com/",
            log_source_id="src",
            log_source_token="tok",
            flush_interval=3600.0,
            batch_size=1000,
        )
    try:
        yield h, h._session
    finally:
        h.close()


def test_the_trailing_slash_is_not_doubled_into_the_endpoint(panther):
    h, _ = panther
    assert h._endpoint == "https://panther.example.com/logsources/src/events"


def test_a_record_that_is_not_json_is_shipped_as_a_message(panther, monkeypatch):
    h, _ = panther
    monkeypatch.setattr(h, "format", lambda rec: "plain text, not json")
    h.emit(record())
    assert json.loads(h._buffer[0]) == {"message": "plain text, not json"}


def test_a_full_batch_wakes_the_shipper(panther):
    h, _ = panther
    h._batch_size = 2
    h._flush_now.clear()
    h.emit(record("a"))
    assert not h._flush_now.is_set()
    h.emit(record("b"))
    assert h._flush_now.is_set()


def test_a_record_that_cannot_be_formatted_is_handled(panther, monkeypatch):
    h, _ = panther
    monkeypatch.setattr(h, "format", MagicMock(side_effect=RuntimeError("formatter died")))
    handled = MagicMock()
    monkeypatch.setattr(h, "handleError", handled)
    h.emit(record())
    handled.assert_called_once()


def test_close_survives_a_session_that_refuses_to_close():
    session = MagicMock()
    session.close.side_effect = RuntimeError("socket already gone")
    with patch.object(panther_mod, "_build_session", return_value=session):
        h = PantherHandler(
            api_host="https://p", log_source_id="s", log_source_token="t", flush_interval=3600.0
        )
    h.close()  # must not raise
    session.close.assert_called_once()


def test_a_buffered_line_that_is_not_json_still_ships_as_an_event(panther):
    h, session = panther
    session.post.return_value = MagicMock(status_code=200)
    assert h._ship(["{not json"]).count == 1
    sent = json.loads(session.post.call_args.kwargs["data"])
    assert sent["events"] == [{"message": "{not json"}]


def test_shipping_nothing_makes_no_request(panther):
    h, session = panther
    assert h._ship([]).count == 0
    session.post.assert_not_called()


def test_a_payload_over_the_threshold_is_gzipped(panther):
    h, session = panther
    h.gzip_threshold = 10
    session.post.return_value = MagicMock(status_code=200)
    h._ship([json.dumps({"m": "x" * 100})])

    kwargs = session.post.call_args.kwargs
    assert kwargs["headers"]["Content-Encoding"] == "gzip"
    assert json.loads(gzip.decompress(kwargs["data"]))["events"][0]["m"] == "x" * 100


class TestPantherSearch:
    @pytest.fixture
    def client(self):
        with patch.object(panther_mod, "_build_session", return_value=MagicMock()):
            c = PantherSearchClient(api_host="https://panther.example.com/", api_key="k")
        return c, c._session

    def test_a_successful_search_returns_its_events(self, client):
        c, session = client
        session.post.return_value = MagicMock(
            status_code=200, json=lambda: {"data": {"search": {"events": [{"id": "1"}]}}}
        )
        assert c.search("field = 'x'", limit=5) == [{"id": "1"}]
        assert c._session.post.call_args.kwargs["headers"]["X-API-Key"] == "k"

    def test_a_non_200_yields_no_events_rather_than_an_error(self, client):
        c, session = client
        session.post.return_value = MagicMock(status_code=403)
        assert c.search("anything") == []

    def test_a_transport_failure_yields_no_events(self, client):
        c, session = client
        session.post.side_effect = RuntimeError("connection reset")
        assert c.search("anything") == []

    def test_close_survives_a_session_that_refuses_to_close(self, client):
        c, session = client
        session.close.side_effect = RuntimeError("already closed")
        c.close()  # must not raise

    def test_the_factory_needs_both_a_host_and_a_key(self, monkeypatch):
        assert make_panther_search_client() is None
        monkeypatch.setenv("PANTHER_API_HOST", "https://panther.example.com")
        assert make_panther_search_client() is None

    def test_without_requests_there_is_no_search_client(self, monkeypatch):
        monkeypatch.setenv("PANTHER_API_HOST", "https://panther.example.com")
        monkeypatch.setenv("PANTHER_API_KEY", "k")
        with patch.object(panther_mod, "_build_session", side_effect=ImportError("no requests")):
            assert make_panther_search_client() is None


# ═══════════════════════════════════════════════════════════════ ADX


def test_adx_builds_its_ingest_client_once_from_the_supplied_credential():
    h = AdxHandler(
        cluster_uri="https://cluster.kusto.windows.net",
        database="logs",
        credential=Credential(),
        flush_interval=3600.0,
    )
    try:
        with patch("azure.kusto.ingest.KustoStreamingIngestClient") as client_cls:
            first = h._get_client()
            assert h._get_client() is first  # cached, not rebuilt per flush
        client_cls.assert_called_once()
    finally:
        h.close()


def test_adx_falls_back_to_the_managed_identity_credential(monkeypatch):
    import vibey_bootstrap.identity as identity

    credential = Credential()
    monkeypatch.setattr(identity, "build_credential", lambda: credential)
    h = AdxHandler(
        cluster_uri="https://cluster.kusto.windows.net", database="logs", flush_interval=3600.0
    )
    try:
        with (
            patch("azure.kusto.ingest.KustoStreamingIngestClient") as client_cls,
            patch(
                "azure.kusto.data.KustoConnectionStringBuilder.with_azure_token_credential"
            ) as kcsb,
        ):
            h._get_client()
        assert kcsb.call_args.args[1] is credential
        client_cls.assert_called_once()
    finally:
        h.close()


def test_an_adx_ingest_failure_is_reported_not_raised():
    h = AdxHandler(
        cluster_uri="https://c.kusto.windows.net",
        database="logs",
        credential=Credential(),
        flush_interval=3600.0,
    )
    try:
        client = MagicMock()
        client.ingest_from_stream.side_effect = RuntimeError("cluster is throttling")
        h._client = client
        result = h._ship([json.dumps({"m": 1})])
        assert (result.ok, result.count) == (False, 0)
    finally:
        h.close()


def test_adx_ships_the_batch_as_multijson():
    h = AdxHandler(
        cluster_uri="https://c.kusto.windows.net",
        database="logs",
        table="Audit",
        credential=Credential(),
        flush_interval=3600.0,
    )
    try:
        h._client = MagicMock()
        _reset_counters()
        assert h._ship(['{"m":1}', '{"m":2}']).count == 2
        props = h._client.ingest_from_stream.call_args.kwargs["ingestion_properties"]
        assert (props.database, props.table) == ("logs", "Audit")
        assert counter_snapshot()["adx.transport.flushes"] == 1
    finally:
        h.close()


class TestAdxFactory:
    def test_a_cluster_without_a_database_is_not_enough(self, monkeypatch):
        monkeypatch.setenv("ADX_CLUSTER_URI", "https://c.kusto.windows.net")
        assert make_adx_handler() is None

    def test_without_the_kusto_extra_the_transport_disables_itself(self, monkeypatch, caplog):
        monkeypatch.setenv("ADX_CLUSTER_URI", "https://c.kusto.windows.net")
        monkeypatch.setenv("ADX_DATABASE", "logs")
        with (
            patch.object(adx_mod, "AdxHandler", side_effect=ImportError("no azure-kusto")),
            caplog.at_level(logging.DEBUG),
        ):
            assert make_adx_handler() is None
        assert "adxlog" in caplog.text


@pytest.mark.parametrize(
    "resolver, default, raw, expected",
    [
        (adx_mod._int_env, 200, "junk", 200),
        (adx_mod._float_env, 5.0, "junk", 5.0),
        (eh_mod._int_env, 100, "junk", 100),
        (eh_mod._float_env, 5.0, "junk", 5.0),
        (panther_mod._int_env, 500, "junk", 500),
        (panther_mod._float_env, 5.0, "junk", 5.0),
    ],
)
def test_cloud_env_helpers_fall_back_on_junk(monkeypatch, resolver, default, raw, expected):
    monkeypatch.setenv("X_CLOUD", raw)
    assert resolver("X_CLOUD", default) == expected


# ═══════════════════════════════════════════════════════════ Event Hubs


def test_event_hubs_builds_its_producer_once_from_the_supplied_credential():
    h = EventHubsHandler(
        fully_qualified_namespace="ns.servicebus.windows.net",
        eventhub_name="logs",
        credential=Credential(),
        flush_interval=3600.0,
    )
    try:
        with patch("azure.eventhub.EventHubProducerClient") as producer_cls:
            first = h._get_producer()
            assert h._get_producer() is first
        producer_cls.assert_called_once()
        assert producer_cls.call_args.kwargs["eventhub_name"] == "logs"
    finally:
        h.close()


def test_event_hubs_falls_back_to_the_managed_identity_credential(monkeypatch):
    import vibey_bootstrap.identity as identity

    credential = Credential()
    monkeypatch.setattr(identity, "build_credential", lambda: credential)
    h = EventHubsHandler(
        fully_qualified_namespace="ns.servicebus.windows.net",
        eventhub_name="logs",
        flush_interval=3600.0,
    )
    try:
        with patch("azure.eventhub.EventHubProducerClient") as producer_cls:
            h._get_producer()
        assert producer_cls.call_args.kwargs["credential"] is credential
    finally:
        h.close()


class TestEventHubsFactory:
    def test_a_namespace_without_a_hub_name_is_not_enough(self, monkeypatch):
        monkeypatch.setenv("EVENTHUB_FQNS", "ns.servicebus.windows.net")
        assert make_event_hubs_handler() is None

    def test_without_the_eventhubs_extra_the_transport_disables_itself(self, monkeypatch, caplog):
        monkeypatch.setenv("EVENTHUB_FQNS", "ns.servicebus.windows.net")
        monkeypatch.setenv("EVENTHUB_NAME", "logs")
        with (
            patch.object(eh_mod, "EventHubsHandler", side_effect=ImportError("no azure-eventhub")),
            caplog.at_level(logging.DEBUG),
        ):
            assert make_event_hubs_handler() is None
        assert "eventhubslog" in caplog.text


def test_adx_ships_nothing_for_an_empty_batch():
    h = AdxHandler(
        cluster_uri="https://c.kusto.windows.net",
        database="logs",
        credential=Credential(),
        flush_interval=3600.0,
    )
    try:
        h._client = MagicMock()
        assert h._ship([]).count == 0
        h._client.ingest_from_stream.assert_not_called()
    finally:
        h.close()


def test_event_hubs_sends_one_batch_per_flush():
    h = EventHubsHandler(
        fully_qualified_namespace="ns.servicebus.windows.net",
        eventhub_name="logs",
        credential=Credential(),
        flush_interval=3600.0,
    )
    try:
        producer = MagicMock()
        h._producer = producer
        _reset_counters()
        assert h._ship(['{"m":1}', '{"m":2}']).count == 2
        assert producer.create_batch.return_value.add.call_count == 2
        producer.send_batch.assert_called_once_with(producer.create_batch.return_value)
        assert counter_snapshot()["event_hubs.transport.flushes"] == 1
    finally:
        h.close()


def test_event_hubs_ships_nothing_for_an_empty_batch():
    h = EventHubsHandler(
        fully_qualified_namespace="ns.servicebus.windows.net",
        eventhub_name="logs",
        credential=Credential(),
        flush_interval=3600.0,
    )
    try:
        h._producer = MagicMock()
        assert h._ship([]).count == 0
        h._producer.send_batch.assert_not_called()
    finally:
        h.close()


def test_an_event_hubs_send_failure_is_reported_not_raised():
    h = EventHubsHandler(
        fully_qualified_namespace="ns.servicebus.windows.net",
        eventhub_name="logs",
        credential=Credential(),
        flush_interval=3600.0,
    )
    try:
        producer = MagicMock()
        producer.send_batch.side_effect = RuntimeError("namespace unreachable")
        h._producer = producer
        result = h._ship(['{"m":1}'])
        assert (result.ok, result.count) == (False, 0)
    finally:
        h.close()


def test_closing_event_hubs_closes_the_producer_and_survives_it_failing():
    h = EventHubsHandler(
        fully_qualified_namespace="ns.servicebus.windows.net",
        eventhub_name="logs",
        credential=Credential(),
        flush_interval=3600.0,
    )
    producer = MagicMock()
    producer.close.side_effect = RuntimeError("link already detached")
    h._producer = producer
    h.close()  # must not raise
    producer.close.assert_called_once()


def test_closing_event_hubs_that_never_produced_anything_is_a_no_op():
    h = EventHubsHandler(
        fully_qualified_namespace="ns.servicebus.windows.net",
        eventhub_name="logs",
        credential=Credential(),
        flush_interval=3600.0,
    )
    h.close()
    assert h._producer is None


def test_a_panther_post_that_never_completes_is_reported_not_raised(panther):
    h, session = panther
    session.post.side_effect = RuntimeError("connection reset by peer")
    result = h._ship([json.dumps({"m": 1})])
    assert (result.ok, result.count) == (False, 0)


def test_a_throttled_panther_post_is_counted_and_retried_later(panther):
    h, session = panther
    session.post.return_value = MagicMock(status_code=429)
    _reset_counters()
    result = h._ship([json.dumps({"m": 1})])
    assert (result.ok, result.count) == (False, 0)
    assert counter_snapshot()["panther.transport.throttled"] == 1


def test_the_panther_session_retries_the_statuses_that_are_worth_retrying():
    session = panther_mod._build_session()
    try:
        adapter = session.get_adapter("https://panther.example.com")
        retry = adapter.max_retries
        assert retry.total == 5
        assert set(retry.status_forcelist) == {408, 429, 500, 502, 503, 504}
        assert retry.allowed_methods == frozenset(["POST"])
        assert retry.raise_on_status is False  # a 500 is a ShipResult, not an exception
    finally:
        session.close()


def test_the_correlation_id_is_stamped_onto_every_panther_event(panther):
    from vibey_bootstrap.logging.correlation import correlation_scope

    h, _ = panther
    with correlation_scope("abc-123"):
        h.emit(record())
    assert json.loads(h._buffer[-1])["p_correlation_id"] == "abc-123"


def test_a_full_panther_buffer_drops_and_counts(panther):
    h, _ = panther
    h._buffer = type(h._buffer)(maxlen=1)
    _reset_counters()
    h.emit(record("a"))
    h.emit(record("b"))
    assert counter_snapshot()["panther.transport.dropped"] == 1


def test_without_requests_the_panther_transport_disables_itself(monkeypatch, caplog):
    from vibey_bootstrap.transports.panther import make_panther_handler

    monkeypatch.setenv("PANTHER_API_HOST", "https://panther.example.com")
    monkeypatch.setenv("PANTHER_LOG_SOURCE_ID", "src")
    monkeypatch.setenv("PANTHER_LOG_SOURCE_TOKEN", "tok")
    with (
        patch.object(panther_mod, "PantherHandler", side_effect=ImportError("no requests")),
        caplog.at_level(logging.DEBUG),
    ):
        assert make_panther_handler() is None
    assert "[panther] extra" in caplog.text
