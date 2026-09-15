"""The NoSqlHandler paths a happy-path flush never reaches.

A logging transport is judged by what it does when things go wrong: it must lose the
record rather than the process. Every test here breaks something on purpose.
"""

from __future__ import annotations

import json
import logging
from unittest.mock import MagicMock, patch

import mongomock
import pytest

from vibey_bootstrap.counters import _reset_counters, counter_snapshot
from vibey_bootstrap.transports import nosql
from vibey_bootstrap.transports.nosql import NoSqlHandler, make_nosql_handler


def record(msg: str = "hi", **extra) -> logging.LogRecord:
    rec = logging.LogRecord("svc", logging.INFO, __file__, 1, msg, None, None)
    for key, value in extra.items():
        setattr(rec, key, value)
    return rec


@pytest.fixture
def handler():
    """A handler wired to a mock collection, with the flush thread effectively parked."""
    collection, client = MagicMock(), MagicMock()
    with patch.object(nosql, "_connect", return_value=(client, collection)):
        h = NoSqlHandler(uri="mongodb://x", database="logs", flush_interval=3600.0, batch_size=1000)
    try:
        yield h, collection, client
    finally:
        h.close()


def test_a_full_buffer_drops_the_oldest_record_and_counts_it(handler):
    h, _, _ = handler
    _reset_counters()
    h._buffer.clear()
    h._buffer = type(h._buffer)(maxlen=2)
    for i in range(4):
        h.emit(record(f"m{i}"))
    assert counter_snapshot()["nosql.transport.dropped"] == 2
    assert len(h._buffer) == 2


def test_an_unserialisable_record_is_handled_not_raised(handler, monkeypatch):
    h, _, _ = handler
    monkeypatch.setattr(h, "_record_to_doc", MagicMock(side_effect=RuntimeError("boom")))
    handled = MagicMock()
    monkeypatch.setattr(h, "handleError", handled)
    h.emit(record())
    handled.assert_called_once()


def test_close_survives_a_client_that_refuses_to_close():
    collection, client = MagicMock(), MagicMock()
    client.close.side_effect = RuntimeError("connection already gone")
    with patch.object(nosql, "_connect", return_value=(client, collection)):
        h = NoSqlHandler(uri="mongodb://x", database="logs", flush_interval=3600.0)
    h.close()  # must not raise
    client.close.assert_called_once()


def test_ship_discards_unparsable_lines_and_ships_the_rest(handler):
    h, collection, _ = handler
    result = h._ship(["{not json", json.dumps({"ts": "2024-01-02T03:04:05+00:00", "m": 1})])
    assert result.ok and result.count == 1
    docs = collection.insert_many.call_args.args[0]
    assert docs[0]["ts"].year == 2024  # the ISO string became a real datetime


def test_a_batch_of_nothing_but_junk_ships_nothing(handler):
    h, collection, _ = handler
    result = h._ship(["{not json", "also not json"])
    assert result.ok and result.count == 0
    collection.insert_many.assert_not_called()


def test_a_failed_insert_is_reported_not_raised(handler):
    h, collection, _ = handler
    collection.insert_many.side_effect = RuntimeError("cosmos said no")
    result = h._ship([json.dumps({"m": 1})])
    assert result.ok is False and result.count == 0


def test_the_ttl_index_is_created_once():
    collection, client = MagicMock(), MagicMock()
    with patch.object(nosql, "_connect", return_value=(client, collection)):
        h = NoSqlHandler(uri="mongodb://x", database="logs", ttl_seconds=60, flush_interval=3600.0)
    try:
        h._ship([json.dumps({"m": 1})])
        h._ship([json.dumps({"m": 2})])
    finally:
        h.close()
    collection.create_index.assert_called_once()
    assert collection.create_index.call_args.kwargs["expireAfterSeconds"] == 60


def test_an_index_the_server_rejects_is_not_retried_every_flush():
    collection, client = MagicMock(), MagicMock()
    collection.create_index.side_effect = RuntimeError("no index for you")
    with patch.object(nosql, "_connect", return_value=(client, collection)):
        h = NoSqlHandler(uri="mongodb://x", database="logs", ttl_seconds=60, flush_interval=3600.0)
    try:
        h._ship([json.dumps({"m": 1})])
        h._ship([json.dumps({"m": 2})])
    finally:
        h.close()
    collection.create_index.assert_called_once()


def test_extra_attributes_are_carried_across_and_stringified(handler):
    h, _, _ = handler
    doc = h._record_to_doc(record("hi", tenant="acme", attempt=3, payload={"a": 1}))
    assert doc["extra"]["tenant"] == "acme"
    assert doc["extra"]["attempt"] == 3
    assert doc["extra"]["payload"] == "{'a': 1}"  # not JSON-able, so str()
    assert "_private" not in doc["extra"]


def test_a_record_with_nothing_extra_gets_no_extra_key(handler):
    h, _, _ = handler
    assert "extra" not in h._record_to_doc(record())


def test_connect_builds_a_client_a_database_and_a_collection(monkeypatch):
    import pymongo

    monkeypatch.setattr(pymongo, "MongoClient", mongomock.MongoClient)
    client, collection = nosql._connect("mongodb://server", "logs", "app_logs", 1_000)
    collection.insert_one({"m": 1})
    assert collection.name == "app_logs"
    assert collection.database.name == "logs"
    assert client["logs"]["app_logs"].count_documents({}) == 1


class TestTheFactory:
    def test_without_a_uri_there_is_no_handler(self):
        assert make_nosql_handler() is None

    def test_a_uri_without_a_database_is_refused(self, monkeypatch):
        monkeypatch.setenv("NOSQL_LOG_URI", "mongodb://x")
        assert make_nosql_handler() is None

    def test_a_configured_transport_is_built(self, monkeypatch):
        monkeypatch.setenv("NOSQL_LOG_URI", "mongodb://x")
        monkeypatch.setenv("NOSQL_LOG_DATABASE", "logs")
        monkeypatch.setenv("NOSQL_LOG_COLLECTION", "audit")
        monkeypatch.setenv("NOSQL_LOG_TTL_SECONDS", "90")
        monkeypatch.setenv("NOSQL_LOG_BATCH_SIZE", "7")
        monkeypatch.setenv("NOSQL_LOG_FLUSH_INTERVAL", "3600")
        monkeypatch.setenv("NOSQL_LOG_MAX_BUFFER", "11")
        monkeypatch.setenv("NOSQL_LOG_CONNECT_TIMEOUT_MS", "250")
        with patch.object(nosql, "_connect", return_value=(MagicMock(), MagicMock())):
            h = make_nosql_handler()
        assert isinstance(h, NoSqlHandler)
        try:
            assert (h.collection_name, h.ttl_seconds, h.batch_size) == ("audit", 90, 7)
            assert (h.connect_timeout_ms, h._buffer.maxlen) == (250, 11)
        finally:
            h.close()

    def test_a_nonsense_ttl_warns_and_disables_the_index(self, monkeypatch, caplog):
        monkeypatch.setenv("NOSQL_LOG_URI", "mongodb://x")
        monkeypatch.setenv("NOSQL_LOG_DATABASE", "logs")
        monkeypatch.setenv("NOSQL_LOG_TTL_SECONDS", "forever")
        monkeypatch.setenv("NOSQL_LOG_FLUSH_INTERVAL", "3600")
        with (
            caplog.at_level(logging.WARNING),
            patch.object(nosql, "_connect", return_value=(MagicMock(), MagicMock())),
        ):
            h = make_nosql_handler()
        try:
            assert h.ttl_seconds is None
            assert "not a valid integer" in caplog.text
        finally:
            h.close()

    def test_without_pymongo_the_transport_disables_itself(self, monkeypatch):
        monkeypatch.setenv("NOSQL_LOG_URI", "mongodb://x")
        monkeypatch.setenv("NOSQL_LOG_DATABASE", "logs")
        with patch.object(nosql, "_connect", side_effect=ImportError("no pymongo")):
            assert make_nosql_handler() is None


@pytest.mark.parametrize("raw, expected", [(None, 200), ("", 200), ("12", 12), ("lots", 200)])
def test_int_env_falls_back_on_anything_it_cannot_parse(monkeypatch, raw, expected):
    if raw is None:
        monkeypatch.delenv("X_INT", raising=False)
    else:
        monkeypatch.setenv("X_INT", raw)
    assert nosql._int_env("X_INT", 200) == expected


@pytest.mark.parametrize("raw, expected", [(None, 5.0), ("", 5.0), ("1.5", 1.5), ("soon", 5.0)])
def test_float_env_falls_back_on_anything_it_cannot_parse(monkeypatch, raw, expected):
    if raw is None:
        monkeypatch.delenv("X_FLOAT", raising=False)
    else:
        monkeypatch.setenv("X_FLOAT", raw)
    assert nosql._float_env("X_FLOAT", 5.0) == expected


def test_a_full_batch_wakes_the_flush_thread_immediately():
    collection, client = MagicMock(), MagicMock()
    with patch.object(nosql, "_connect", return_value=(client, collection)):
        h = NoSqlHandler(uri="mongodb://x", database="logs", batch_size=2, flush_interval=3600.0)
    try:
        h._flush_now.clear()
        h.emit(record("one"))
        assert not h._flush_now.is_set()  # below the batch size: wait for the interval
        h.emit(record("two"))
        assert h._flush_now.is_set()  # at it: ship now rather than in an hour
    finally:
        h.close()


def test_an_attribute_that_cannot_even_be_stringified_is_dropped_not_fatal(handler):
    h, _, _ = handler

    class Unprintable:
        def __str__(self) -> str:
            raise RuntimeError("I refuse")

    doc = h._record_to_doc(record("hi", good="kept", bad=Unprintable()))
    assert doc["extra"] == {"good": "kept"}
