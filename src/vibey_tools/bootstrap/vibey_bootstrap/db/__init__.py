"""Relational database access layer — SQLAlchemy 2 engine/session factory."""

from __future__ import annotations

import logging
import os
import threading
import time
from collections.abc import Generator
from typing import Any

from vibey_bootstrap.failclose import fail_open_env, require_env

_logger = logging.getLogger(__name__)

_engine: Any = None
_sessionmaker: Any = None
_lock = threading.Lock()


def create_engine_from_env(*, dsn_env: str = "DATABASE_URL", **kwargs: Any) -> Any:
    """Build a SQLAlchemy engine from ``DATABASE_URL`` (or custom env var)."""
    from sqlalchemy import create_engine  # type: ignore[import-untyped]

    dsn = require_env(dsn_env)
    defaults: dict[str, Any] = {"pool_pre_ping": True, "future": True}
    defaults.update(kwargs)
    if not str(dsn).lower().startswith("sqlite"):
        defaults["pool_size"] = int(defaults.get("pool_size", 5))
        defaults["max_overflow"] = int(defaults.get("max_overflow", 10))
    return create_engine(dsn, **defaults)


def get_engine(*, dsn_env: str = "DATABASE_URL", **kwargs: Any) -> Any:
    """Lazy singleton engine."""
    global _engine, _sessionmaker
    with _lock:
        if _engine is None:
            _engine = create_engine_from_env(dsn_env=dsn_env, **kwargs)
            from sqlalchemy.orm import sessionmaker  # type: ignore[import-untyped]

            _sessionmaker = sessionmaker(bind=_engine, expire_on_commit=False)
        return _engine


def get_sessionmaker(*, dsn_env: str = "DATABASE_URL", **kwargs: Any) -> Any:
    get_engine(dsn_env=dsn_env, **kwargs)
    assert _sessionmaker is not None
    return _sessionmaker


def get_db(*, dsn_env: str = "DATABASE_URL") -> Generator[Any, None, None]:
    """FastAPI-style session dependency — yields and always closes."""
    Session = get_sessionmaker(dsn_env=dsn_env)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def db_health(*, dsn_env: str = "DATABASE_URL") -> dict[str, Any]:
    """Return ``{status, latency_ms}`` for health probes."""
    from sqlalchemy import text  # type: ignore[import-untyped]

    start = time.perf_counter()
    try:
        engine = get_engine(dsn_env=dsn_env)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        latency = (time.perf_counter() - start) * 1000
        return {"status": "ok", "latency_ms": round(latency, 2)}
    except Exception as exc:
        return {"status": "error", "latency_ms": None, "error": str(exc)}


def postgres_rls_statements(table: str, tenant_col: str = "tenant_id") -> list[str]:
    """Idempotent RLS DDL for multi-tenant Postgres tables."""
    return [
        f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;",
        f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;",
        f"""CREATE POLICY IF NOT EXISTS tenant_isolation ON {table}
            USING ({tenant_col} = current_setting('app.current_tenant_id', true));""",
    ]


def _reset_db() -> None:
    if os.environ.get("AZURE_BOOTSTRAP_ALLOW_RESET") != "1":
        raise RuntimeError("_reset_db is test-only")
    global _engine, _sessionmaker
    with _lock:
        if _engine is not None:
            try:
                _engine.dispose()
            except Exception:
                pass
        _engine = None
        _sessionmaker = None


__all__ = [
    "create_engine_from_env",
    "db_health",
    "get_db",
    "get_engine",
    "get_sessionmaker",
    "postgres_rls_statements",
    "_reset_db",
]
