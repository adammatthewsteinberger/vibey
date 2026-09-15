"""SQL and Blob transport paths that only a broken backend reaches.

Both transports are buffered shippers, so the invariant under test is the same one
everywhere: a failing database or storage account degrades logging, never the process.
"""

from __future__ import annotations

import json
import logging
import socket
import sys
from unittest.mock import MagicMock, patch

import pytest

from vibey_bootstrap.transports import blob as blob_mod
from vibey_bootstrap.transports import sql as sql_mod
from vibey_bootstrap.transports.blob import BlobHandler, make_blob_handler
from vibey_bootstrap.transports.sql import SqlHandler, make_sql_handler


def record(msg: str = "hi") -> logging.LogRecord:
    return logging.LogRecord("svc", logging.INFO, __file__, 1, msg, None, None)


def engine_stub() -> tuple[MagicMock, MagicMock]:
    engine, conn = MagicMock(), MagicMock()
    engine.begin.return_value.__enter__ = MagicMock(return_value=conn)
    engine.begin.return_value.__exit__ = MagicMock(return_value=False)
    return engine, conn


# ═══════════════════════════════════════════════════════════════════ SQL


def test_a_record_the_formatter_mangled_still_produces_a_row():
    row = sql_mod._extract_row(record("fallback"), "this is not json")
    assert row["level"] == "INFO"
    assert row["message"] == "fallback"
    assert row["extra"] == {}
    assert row["correlation_id"] is None


def test_a_table_that_cannot_be_created_does_not_stop_the_handler(caplog):
    engine, conn = engine_stub()
    conn.execute.side_effect = RuntimeError("no CREATE for you")
    with (
        patch.object(sql_mod, "_build_engine", return_value=(engine, MagicMock(), "DDL")),
        caplog.at_level(logging.DEBUG),
    ):
        h = SqlHandler(dsn="sqlite:///:memory:", flush_interval=3600.0, create_table=True)
    h.close()
    assert "ensure_table() failed" in caplog.text


@pytest.fixture
def sql_handler():
    engine, conn = engine_stub()
    with patch.object(sql_mod, "_build_engine", return_value=(engine, MagicMock(), "DDL")):
        h = SqlHandler(dsn="sqlite:///:memory:", flush_interval=3600.0, batch_size=1000)
    try:
        yield h, engine, conn
    finally:
        h.close()


def test_a_full_sql_buffer_drops_and_counts(sql_handler):
    from vibey_bootstrap.counters import _reset_counters, counter_snapshot

    h, _, _ = sql_handler
    _reset_counters()
    h._buffer = type(h._buffer)(maxlen=1)
    h.emit(record("a"))
    h.emit(record("b"))
    assert counter_snapshot()["sql.transport.dropped"] == 1


def test_a_record_that_cannot_be_formatted_is_handled(sql_handler, monkeypatch):
    h, _, _ = sql_handler
    monkeypatch.setattr(h, "format", MagicMock(side_effect=RuntimeError("formatter died")))
    handled = MagicMock()
    monkeypatch.setattr(h, "handleError", handled)
    h.emit(record())
    handled.assert_called_once()


def test_close_survives_an_engine_that_refuses_to_dispose():
    engine, _ = engine_stub()
    engine.dispose.side_effect = RuntimeError("pool already torn down")
    with patch.object(sql_mod, "_build_engine", return_value=(engine, MagicMock(), "DDL")):
        h = SqlHandler(dsn="sqlite:///:memory:", flush_interval=3600.0)
    h.close()  # must not raise
    engine.dispose.assert_called_once()


def test_unparsable_buffer_lines_are_skipped(sql_handler):
    h, _, conn = sql_handler
    good = json.dumps(
        {
            "ts": "t",
            "level": "INFO",
            "logger": "svc",
            "message": "m",
            "correlation_id": None,
            "extra": "{}",
        }
    )
    assert h._ship(["{not json", good]).count == 1
    conn.execute.assert_called_once()


def test_a_batch_of_nothing_but_junk_reaches_no_database(sql_handler):
    h, _, conn = sql_handler
    result = h._ship(["{not json", "also junk"])
    assert (result.ok, result.count) == (True, 0)
    conn.execute.assert_not_called()


class TestEngineConstruction:
    """`_build_engine` branches on the dialect, which decides pooling and the JSON column."""

    def fake_sqlalchemy(self, monkeypatch, dialect: str) -> MagicMock:
        import sqlalchemy

        created = MagicMock()
        engine = MagicMock()
        engine.dialect.name = dialect
        created.return_value = engine
        monkeypatch.setattr(sqlalchemy, "create_engine", created)
        return created

    def test_a_server_dsn_gets_a_bounded_connection_pool(self, monkeypatch):
        created = self.fake_sqlalchemy(monkeypatch, "postgresql")
        _, _, ddl = sql_mod._build_engine(dsn="postgresql://h/db", table="app_logs", pool_size=4)
        assert created.call_args.kwargs == {
            "pool_pre_ping": True,
            "pool_size": 4,
            "max_overflow": 0,
            "pool_timeout": 10,
        }
        assert "extra JSONB" in ddl

    def test_sqlite_is_left_with_its_default_pool(self, monkeypatch):
        created = self.fake_sqlalchemy(monkeypatch, "sqlite")
        _, _, ddl = sql_mod._build_engine(dsn="sqlite:///x.db", table="app_logs", pool_size=4)
        assert created.call_args.kwargs == {"pool_pre_ping": True}
        assert "extra JSON" in ddl and "JSONB" not in ddl

    def test_postgres_without_its_dialect_extras_falls_back_to_plain_json(self, monkeypatch):
        self.fake_sqlalchemy(monkeypatch, "postgresql")
        monkeypatch.setitem(sys.modules, "sqlalchemy.dialects.postgresql", None)
        _, _, ddl = sql_mod._build_engine(dsn="postgresql://h/db", table="app_logs", pool_size=4)
        assert "extra JSONB" in ddl  # the DDL still says JSONB; only the model type fell back


class TestSqlFactory:
    def test_a_table_name_that_is_not_an_identifier_is_refused(self, monkeypatch, caplog):
        monkeypatch.setenv("SQL_LOG_DSN", "sqlite:///:memory:")
        monkeypatch.setenv("SQL_LOG_TABLE", "logs; DROP TABLE users")
        with caplog.at_level(logging.WARNING):
            assert make_sql_handler() is None
        assert "configuration error" in caplog.text

    def test_an_engine_that_will_not_build_disables_the_transport(self, monkeypatch, caplog):
        monkeypatch.setenv("SQL_LOG_DSN", "sqlite:///:memory:")
        with (
            patch.object(sql_mod, "_build_engine", side_effect=RuntimeError("driver exploded")),
            caplog.at_level(logging.DEBUG),
        ):
            assert make_sql_handler() is None
        assert "failed to initialise engine" in caplog.text


@pytest.mark.parametrize(
    "resolver, raw, expected",
    [
        (sql_mod._int_env, "nope", 200),
        (sql_mod._int_env, "3", 3),
        (sql_mod._float_env, "nope", 5.0),
        (sql_mod._float_env, "2.5", 2.5),
    ],
)
def test_sql_env_helpers_fall_back_on_junk(monkeypatch, resolver, raw, expected):
    monkeypatch.setenv("SQL_X", raw)
    assert resolver("SQL_X", 200 if resolver is sql_mod._int_env else 5.0) == expected


# ═══════════════════════════════════════════════════════════════════ Blob


def blob_handler(**kw) -> tuple[BlobHandler, MagicMock, MagicMock]:
    container, client = MagicMock(), MagicMock()
    container.get_blob_client.return_value = client
    kw.setdefault("flush_interval", 3600.0)
    kw.setdefault("batch_size", 1000)
    return BlobHandler(container_client=container, **kw), container, client


def test_shipping_an_empty_batch_touches_no_storage():
    h, container, _ = blob_handler()
    try:
        assert h._ship([]).count == 0
        container.get_blob_client.assert_not_called()
    finally:
        h.close()


def test_an_append_blob_that_already_exists_is_not_an_error():
    h, _, client = blob_handler()
    client.create_append_blob.side_effect = RuntimeError("BlobAlreadyExists")
    try:
        h.emit(record())
        h.flush()
    finally:
        h.close()
    client.append_block.assert_called_once()


def test_daily_rolling_names_the_blob_by_date_not_hour():
    h, _, _ = blob_handler(roll="day")
    try:
        window = h._window_key()
        assert len(window) == 8 and window.isdigit()
        assert h._blob_name_append(window).endswith(f"-{window}.jsonl")
    finally:
        h.close()


def test_a_hostname_lookup_that_fails_still_yields_a_usable_name(monkeypatch):
    monkeypatch.setattr(socket, "gethostname", MagicMock(side_effect=OSError("no DNS")))
    assert blob_mod._safe_hostname() == "host"


class TestContainerClientConstruction:
    def test_an_account_url_uses_the_managed_identity_credential(self, monkeypatch):
        import vibey_bootstrap.identity as identity

        class Credential:  # the shape azure-storage-blob requires
            def get_token(self, *scopes, **kw):  # pragma: no cover - never called
                raise AssertionError("no request is made in this test")

        credential = Credential()
        monkeypatch.setattr(identity, "build_credential", lambda: credential)
        client = blob_mod._build_container_client(
            container="logs", account_url="https://acct.blob.core.windows.net", conn_str=None
        )
        assert client.container_name == "logs"
        assert client.credential is credential

    def test_a_connection_string_is_used_when_there_is_no_account_url(self):
        conn = (
            "DefaultEndpointsProtocol=https;AccountName=acct;"
            "AccountKey=aGVsbG8=;EndpointSuffix=core.windows.net"
        )
        client = blob_mod._build_container_client(container="logs", account_url=None, conn_str=conn)
        assert client.container_name == "logs"

    def test_neither_is_a_configuration_error(self):
        with pytest.raises(ValueError, match="account_url or conn_str"):
            blob_mod._build_container_client(container="logs", account_url=None, conn_str=None)


class TestBlobFactory:
    def test_a_container_with_no_endpoint_is_not_enough(self, monkeypatch):
        monkeypatch.setenv("BLOB_LOG_CONTAINER", "logs")
        assert make_blob_handler() is None

    def test_a_client_that_will_not_build_disables_the_transport(self, monkeypatch, caplog):
        monkeypatch.setenv("BLOB_LOG_CONTAINER", "logs")
        monkeypatch.setenv("BLOB_LOG_ACCOUNT_URL", "https://acct.blob.core.windows.net")
        with (
            patch.object(
                blob_mod,
                "_build_container_client",
                side_effect=RuntimeError("credential chain exhausted"),
            ),
            caplog.at_level(logging.DEBUG),
        ):
            assert make_blob_handler() is None
        assert "failed to build container client" in caplog.text

    def test_a_configured_transport_is_built_from_the_environment(self, monkeypatch):
        monkeypatch.setenv("BLOB_LOG_CONTAINER", "logs")
        monkeypatch.setenv("BLOB_LOG_ACCOUNT_URL", "https://acct.blob.core.windows.net")
        monkeypatch.setenv("BLOB_LOG_PREFIX", "/audit/")
        monkeypatch.setenv("BLOB_LOG_MODE", "BLOCK")
        monkeypatch.setenv("BLOB_LOG_ROLL", "DAY")
        monkeypatch.setenv("BLOB_BATCH_SIZE", "9")
        monkeypatch.setenv("BLOB_FLUSH_INTERVAL", "3600")
        monkeypatch.setenv("BLOB_MAX_BUFFER", "13")
        with patch.object(blob_mod, "_build_container_client", return_value=MagicMock()):
            h = make_blob_handler()
        try:
            assert isinstance(h, BlobHandler)
            assert (h._prefix, h._mode, h._roll) == ("audit", "block", "day")
            assert (h.batch_size, h._buffer.maxlen) == (9, 13)
        finally:
            h.close()


@pytest.mark.parametrize(
    "resolver, raw, expected",
    [
        (blob_mod._int_env, "nope", 200),
        (blob_mod._int_env, "3", 3),
        (blob_mod._float_env, "nope", 5.0),
        (blob_mod._float_env, "2.5", 2.5),
    ],
)
def test_blob_env_helpers_fall_back_on_junk(monkeypatch, resolver, raw, expected):
    monkeypatch.setenv("BLOB_X", raw)
    assert resolver("BLOB_X", 200 if resolver is blob_mod._int_env else 5.0) == expected


def test_a_full_sql_batch_wakes_the_shipper_immediately():
    engine, _ = engine_stub()
    with patch.object(sql_mod, "_build_engine", return_value=(engine, MagicMock(), "DDL")):
        h = SqlHandler(dsn="sqlite:///:memory:", flush_interval=3600.0, batch_size=2)
    try:
        h._flush_now.clear()
        h.emit(record("one"))
        assert not h._flush_now.is_set()  # below the batch size: wait for the interval
        h.emit(record("two"))
        assert h._flush_now.is_set()  # at it: ship now rather than in an hour
    finally:
        h.close()
