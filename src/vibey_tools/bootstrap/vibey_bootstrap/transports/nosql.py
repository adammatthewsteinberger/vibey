# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""NoSQL (Cosmos DB / MongoDB) logging transport — buffered document shipper."""

from __future__ import annotations

import datetime
import json
import logging
from typing import Any

from vibey_bootstrap.counters import bump_counter
from vibey_bootstrap.failclose import fail_open_env, optional_env
from vibey_bootstrap.logging.correlation import CorrelationFilter, get_correlation_id
from vibey_bootstrap.logging.jsonformatter import JsonLogFormatter
from vibey_bootstrap.transports._base import ShipResult, _BufferedShipper

_COUNTER_FLUSHES = "nosql.transport.flushes"

_STANDARD_ATTRS = frozenset(
    {
        "args",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "message",
        "module",
        "msecs",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "taskName",
        "thread",
        "threadName",
    }
)


class NoSqlHandler(_BufferedShipper):
    """Buffered handler that ships log records to a MongoDB / Cosmos DB collection."""

    _THREAD_NAME = "nosql-transport"

    def __init__(
        self,
        *,
        uri: str,
        database: str,
        collection: str = "app_logs",
        ttl_seconds: int | None = None,
        batch_size: int = 200,
        flush_interval: float = 5.0,
        max_buffer: int = 10_000,
        connect_timeout_ms: int = 5_000,
    ) -> None:
        super().__init__(
            counter_prefix="nosql",
            batch_size=batch_size,
            flush_interval=flush_interval,
            max_buffer=max_buffer,
        )
        self.uri = uri
        self.database = database
        self.collection_name = collection
        self.ttl_seconds = ttl_seconds
        self.batch_size = self._batch_size
        self.flush_interval = flush_interval
        self.connect_timeout_ms = connect_timeout_ms

        self.setFormatter(JsonLogFormatter())
        self.addFilter(CorrelationFilter())

        self._client, self._collection = _connect(uri, database, collection, connect_timeout_ms)
        self._ttl_ensured = False

    def emit(self, record: logging.LogRecord) -> None:
        try:
            doc = self._record_to_doc(record)
            line = json.dumps(doc, default=str)
            maxlen = self._buffer.maxlen or 0
            with self._lock:
                was_full = maxlen > 0 and len(self._buffer) >= maxlen
                self._buffer.append(line)
                current_size = len(self._buffer)
            if was_full:
                bump_counter("nosql.transport.dropped")
            if current_size >= self._batch_size:
                self._flush_now.set()
        except Exception:
            self.handleError(record)

    def _on_close(self) -> None:
        try:
            self._client.close()
        except Exception:
            pass

    def _ship(self, batch: list[str]) -> ShipResult:
        docs: list[dict[str, Any]] = []
        for line in batch:
            try:
                doc = json.loads(line)
                if "ts" in doc and isinstance(doc["ts"], str):
                    doc["ts"] = datetime.datetime.fromisoformat(doc["ts"])
                docs.append(doc)
            except (ValueError, TypeError):
                continue
        if not docs:
            return ShipResult(ok=True, count=0)

        bump_counter(_COUNTER_FLUSHES)
        try:
            self._ensure_ttl_index()
            self._collection.insert_many(docs, ordered=False)
            return ShipResult(ok=True, count=len(docs))
        except Exception:
            return ShipResult(ok=False, count=0)

    def _ensure_ttl_index(self) -> None:
        if self._ttl_ensured or self.ttl_seconds is None:
            return
        try:
            self._collection.create_index(
                [("ts", 1)],
                expireAfterSeconds=self.ttl_seconds,
                background=True,
            )
            self._ttl_ensured = True
        except Exception:
            self._ttl_ensured = True

    def _record_to_doc(self, record: logging.LogRecord) -> dict[str, Any]:
        doc: dict[str, Any] = {
            "ts": datetime.datetime.fromtimestamp(record.created, tz=datetime.UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": get_correlation_id() or getattr(record, "correlation_id", None),
        }
        extra: dict[str, Any] = {}
        for key, value in record.__dict__.items():
            if key.startswith("_") or key in _STANDARD_ATTRS or key in doc:
                continue
            try:
                if isinstance(value, (str, int, float, bool, type(None))):
                    extra[key] = value
                else:
                    extra[key] = str(value)
            except Exception:
                pass
        if extra:
            doc["extra"] = extra
        return doc


def _connect(
    uri: str,
    database: str,
    collection_name: str,
    connect_timeout_ms: int,
) -> tuple[Any, Any]:
    import pymongo  # type: ignore[import-untyped]

    client: Any = pymongo.MongoClient(uri, serverSelectionTimeoutMS=connect_timeout_ms)
    db = client[database]
    collection = db[collection_name]
    return client, collection


def make_nosql_handler() -> logging.Handler | None:
    uri = fail_open_env("NOSQL_LOG_URI")
    if not uri:
        return None

    database = fail_open_env("NOSQL_LOG_DATABASE")
    if not database:
        logging.getLogger(__name__).debug(
            "NOSQL_LOG_URI is set but NOSQL_LOG_DATABASE is unset — NoSQL transport disabled.",
        )
        return None

    ttl_raw = optional_env("NOSQL_LOG_TTL_SECONDS")
    ttl_seconds: int | None = None
    if ttl_raw:
        try:
            ttl_seconds = int(ttl_raw)
        except ValueError:
            logging.getLogger(__name__).warning(
                "NOSQL_LOG_TTL_SECONDS=%r is not a valid integer — TTL index skipped.",
                ttl_raw,
            )

    try:
        return NoSqlHandler(
            uri=uri,
            database=database,
            collection=optional_env("NOSQL_LOG_COLLECTION") or "app_logs",
            ttl_seconds=ttl_seconds,
            batch_size=_int_env("NOSQL_LOG_BATCH_SIZE", 200),
            flush_interval=_float_env("NOSQL_LOG_FLUSH_INTERVAL", 5.0),
            max_buffer=_int_env("NOSQL_LOG_MAX_BUFFER", 10_000),
            connect_timeout_ms=_int_env("NOSQL_LOG_CONNECT_TIMEOUT_MS", 5_000),
        )
    except ImportError:
        logging.getLogger(__name__).debug(
            "NOSQL_LOG_URI set but the [nosqllog] extra (pymongo) is not installed "
            "— NoSQL transport disabled.",
        )
        return None


def _int_env(name: str, default: int) -> int:
    raw = optional_env(name)
    try:
        return int(raw) if raw else default
    except ValueError:
        return default


def _float_env(name: str, default: float) -> float:
    raw = optional_env(name)
    try:
        return float(raw) if raw else default
    except ValueError:
        return default


__all__ = ["NoSqlHandler", "make_nosql_handler"]
