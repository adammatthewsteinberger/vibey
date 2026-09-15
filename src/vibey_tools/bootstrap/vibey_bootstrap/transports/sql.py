"""Relational database logging transport — SQLAlchemy Core INSERT shipper."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from vibey_bootstrap.counters import bump_counter
from vibey_bootstrap.failclose import fail_open_env, optional_env
from vibey_bootstrap.logging.correlation import CorrelationFilter
from vibey_bootstrap.logging.jsonformatter import JsonLogFormatter
from vibey_bootstrap.transports._base import ShipResult, _BufferedShipper

_COUNTER_FLUSHES = "sql.transport.flushes"

_TOP_LEVEL_KEYS = frozenset({"timestamp", "level", "logger", "message", "correlation_id"})


def _extract_row(record: logging.LogRecord, formatted_json: str) -> dict[str, Any]:
    try:
        doc: dict[str, Any] = json.loads(formatted_json)
    except Exception:
        return {
            "ts": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": None,
            "extra": {},
        }

    extra = {k: v for k, v in doc.items() if k not in _TOP_LEVEL_KEYS}
    return {
        "ts": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
        "level": doc.get("level", record.levelname),
        "logger": doc.get("logger", record.name),
        "message": doc.get("message", record.getMessage()),
        "correlation_id": doc.get("correlation_id") or None,
        "extra": extra,
    }


class SqlHandler(_BufferedShipper):
    """Buffered handler that ships log records to a relational database table."""

    _THREAD_NAME = "sql-transport"

    def __init__(
        self,
        *,
        dsn: str,
        table: str = "app_logs",
        pool_size: int = 2,
        batch_size: int = 200,
        flush_interval: float = 5.0,
        max_buffer: int = 10_000,
        create_table: bool = False,
    ) -> None:
        super().__init__(
            counter_prefix="sql",
            batch_size=batch_size,
            flush_interval=flush_interval,
            max_buffer=max_buffer,
        )
        self._table_name = table
        self.batch_size = self._batch_size
        self.flush_interval = flush_interval

        self.setFormatter(JsonLogFormatter())
        self.addFilter(CorrelationFilter())

        self._engine, self._insert_stmt, self._ddl = _build_engine(
            dsn=dsn,
            table=table,
            pool_size=pool_size,
        )

        if create_table:
            try:
                self.ensure_table()
            except Exception:
                logging.getLogger(__name__).debug(
                    "sql transport: ensure_table() failed — table may not exist",
                    exc_info=True,
                )

    def ensure_table(self) -> None:
        from sqlalchemy import text  # type: ignore[import-untyped]

        with self._engine.begin() as conn:
            conn.execute(text(self._ddl))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            formatted = self.format(record)
            row = _extract_row(record, formatted)
            line = json.dumps(row, default=str)
            maxlen = self._buffer.maxlen or 0
            with self._lock:
                was_full = maxlen > 0 and len(self._buffer) >= maxlen
                self._buffer.append(line)
                current_size = len(self._buffer)
            if was_full:
                bump_counter("sql.transport.dropped")
            if current_size >= self._batch_size:
                self._flush_now.set()
        except Exception:
            self.handleError(record)

    def _on_close(self) -> None:
        try:
            self._engine.dispose()
        except Exception:
            pass

    def _ship(self, batch: list[str]) -> ShipResult:
        rows: list[dict[str, Any]] = []
        for line in batch:
            try:
                rows.append(json.loads(line))
            except (ValueError, TypeError):
                continue
        if not rows:
            return ShipResult(ok=True, count=0)

        bump_counter(_COUNTER_FLUSHES)
        params = [
            {
                "ts": r["ts"],
                "level": r["level"],
                "logger": r["logger"],
                "message": r["message"],
                "correlation_id": r["correlation_id"],
                "extra": json.dumps(r["extra"], default=repr) if r["extra"] else "{}",
            }
            for r in rows
        ]

        try:
            with self._engine.begin() as conn:
                conn.execute(self._insert_stmt, params)
            return ShipResult(ok=True, count=len(rows))
        except Exception:
            return ShipResult(ok=False, count=0)


def _build_engine(
    *,
    dsn: str,
    table: str,
    pool_size: int,
) -> tuple[Any, Any, str]:
    from sqlalchemy import (  # type: ignore[import-untyped]
        Column,
        MetaData,
        String,
        Table,
        Text,
        create_engine,
    )
    from sqlalchemy import text as sa_text  # type: ignore[import-untyped]

    _dsn_lower = str(dsn).lower()
    _is_sqlite = _dsn_lower.startswith("sqlite")
    _pool_kwargs: dict[str, Any] = {"pool_pre_ping": True}
    if not _is_sqlite:
        _pool_kwargs["pool_size"] = pool_size
        _pool_kwargs["max_overflow"] = 0
        _pool_kwargs["pool_timeout"] = 10

    engine = create_engine(dsn, **_pool_kwargs)
    dialect_name = engine.dialect.name
    if dialect_name == "postgresql":
        try:
            from sqlalchemy.dialects.postgresql import JSONB  # type: ignore[import-untyped]

            extra_col_type: Any = JSONB
        except Exception:
            from sqlalchemy import JSON  # type: ignore[import-untyped]

            extra_col_type = JSON
    else:
        from sqlalchemy import JSON  # type: ignore[import-untyped]

        extra_col_type = JSON

    metadata = MetaData()
    Table(
        table,
        metadata,
        Column("ts", Text, nullable=False),
        Column("level", String(16), nullable=False),
        Column("logger", Text, nullable=False),
        Column("message", Text, nullable=False),
        Column("correlation_id", Text, nullable=True),
        Column("extra", extra_col_type, nullable=True),
    )

    _validate_identifier(table)
    insert_sql = (
        f"INSERT INTO {table} "  # nosec B608
        "(ts, level, logger, message, correlation_id, extra) "
        "VALUES (:ts, :level, :logger, :message, :correlation_id, :extra)"
    )
    insert_stmt = sa_text(insert_sql)

    if dialect_name == "postgresql":
        extra_col_ddl = "extra JSONB"
    else:
        extra_col_ddl = "extra JSON"

    ddl = (
        f"CREATE TABLE IF NOT EXISTS {table} ("
        "ts TEXT NOT NULL, "
        "level TEXT NOT NULL, "
        "logger TEXT NOT NULL, "
        "message TEXT NOT NULL, "
        "correlation_id TEXT, "
        f"{extra_col_ddl}"
        ")"
    )

    return engine, insert_stmt, ddl


def _validate_identifier(name: str) -> None:
    import re

    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,62}", name):
        raise ValueError(
            f"SQL_LOG_TABLE {name!r} is not a valid SQL identifier. "
            "Use only letters, digits, and underscores (max 63 chars, must start with a letter or underscore)."
        )


def make_sql_handler() -> logging.Handler | None:
    dsn = fail_open_env("SQL_LOG_DSN")
    if not dsn:
        return None

    table = optional_env("SQL_LOG_TABLE") or "app_logs"
    create_table = optional_env("SQL_LOG_CREATE_TABLE") == "1"
    pool_size = _int_env("SQL_LOG_POOL_SIZE", 2)
    batch_size = _int_env("SQL_LOG_BATCH_SIZE", 200)
    flush_interval = _float_env("SQL_LOG_FLUSH_INTERVAL", 5.0)
    max_buffer = _int_env("SQL_LOG_MAX_BUFFER", 10_000)

    try:
        return SqlHandler(
            dsn=dsn,
            table=table,
            pool_size=pool_size,
            batch_size=batch_size,
            flush_interval=flush_interval,
            max_buffer=max_buffer,
            create_table=create_table,
        )
    except ImportError:
        logging.getLogger(__name__).debug(
            "SQL_LOG_DSN is set but the [sqllog] extra (sqlalchemy) is not "
            "installed — sql transport disabled.",
        )
        return None
    except ValueError as exc:
        logging.getLogger(__name__).warning("sql transport: configuration error — %s", exc)
        return None
    except Exception:
        logging.getLogger(__name__).debug(
            "sql transport: failed to initialise engine — transport disabled",
            exc_info=True,
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


__all__ = ["SqlHandler", "make_sql_handler"]
