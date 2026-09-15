"""DB module tests."""

from __future__ import annotations

import pytest

pytest.importorskip("sqlalchemy")

from vibey_bootstrap.db import create_engine_from_env, db_health, postgres_rls_statements


def test_postgres_rls_statements() -> None:
    stmts = postgres_rls_statements("orders")
    assert any("ROW LEVEL SECURITY" in s for s in stmts)


def test_db_health_ok(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    result = db_health()
    assert result["status"] == "ok"


def test_create_engine_from_env(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    engine = create_engine_from_env()
    assert engine is not None
    engine.dispose()
