"""Integration tests with SQLite, mongomock, and Azurite — real I/O, no Azure cloud."""

from __future__ import annotations

import json
import logging

import pytest

pytestmark = pytest.mark.integration


def _record(msg: str = "integration-test") -> logging.LogRecord:
    return logging.LogRecord("integration", logging.INFO, __file__, 1, msg, None, None)


def test_sql_handler_sqlite_roundtrip(sqlite_dsn: str) -> None:
    pytest.importorskip("sqlalchemy")
    from sqlalchemy import create_engine, text

    from vibey_bootstrap.transports.sql import SqlHandler

    h = SqlHandler(
        dsn=sqlite_dsn,
        table="app_logs",
        create_table=True,
        batch_size=5,
        flush_interval=3600.0,
    )
    try:
        for i in range(7):
            h.emit(_record(f"line-{i}"))
        h.flush()
    finally:
        h.close()

    engine = create_engine(sqlite_dsn)
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT message FROM app_logs ORDER BY rowid")).fetchall()
    assert [r[0] for r in rows] == [f"line-{i}" for i in range(7)]


def test_nosql_handler_mongomock_roundtrip() -> None:
    pytest.importorskip("pymongo")
    from unittest.mock import patch

    import mongomock

    from vibey_bootstrap.transports.nosql import NoSqlHandler

    client = mongomock.MongoClient()
    collection = client["testdb"]["app_logs"]
    with patch(
        "vibey_bootstrap.transports.nosql._connect",
        return_value=(client, collection),
    ):
        h = NoSqlHandler(
            uri="mongodb://unused",
            database="testdb",
            collection="app_logs",
            batch_size=3,
            flush_interval=3600.0,
        )
        try:
            for i in range(5):
                h.emit(_record(f"doc-{i}"))
            h.flush()
        finally:
            h.close()

    docs = list(collection.find({}, {"_id": 0, "message": 1}))
    messages = [d["message"] for d in docs]
    # Sorted, not positional: batch_size=3 means the background thread ships the first
    # batch while the main thread is still emitting, so the two batches can land in
    # either order. Insertion order across batches is not a guarantee the handler makes.
    assert sorted(messages) == [f"doc-{i}" for i in range(5)]


def test_blob_handler_azurite_append(azurite_container) -> None:
    from vibey_bootstrap.transports.blob import BlobHandler

    h = BlobHandler(
        container_client=azurite_container,
        prefix="integration",
        mode="append",
        batch_size=10,
        flush_interval=3600.0,
    )
    try:
        h.emit(_record('{"event":"one"}'))
        h.emit(_record('{"event":"two"}'))
        h.flush()
    finally:
        h.close()

    blobs = list(azurite_container.list_blobs(name_starts_with="integration/"))
    assert blobs, "expected at least one append blob"
    blob = azurite_container.get_blob_client(blobs[0].name)
    body = blob.download_blob().readall().decode()
    lines = [json.loads(line) for line in body.strip().split("\n") if line]
    assert len(lines) >= 2
    assert lines[0].get("message") == '{"event":"one"}' or "event" in str(lines[0])
