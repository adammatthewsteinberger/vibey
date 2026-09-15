"""DocumentDB tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from vibey_bootstrap.documentdb import documentdb_health


def test_documentdb_health_error_without_uri(monkeypatch) -> None:
    monkeypatch.delenv("NOSQL_URI", raising=False)
    result = documentdb_health()
    assert result["status"] == "error"


def test_documentdb_health_ok(monkeypatch) -> None:
    pytest.importorskip("pymongo")
    monkeypatch.setenv("NOSQL_URI", "mongodb://localhost:27017")
    monkeypatch.setenv("NOSQL_DATABASE", "admin")
    client = MagicMock()
    with patch("vibey_bootstrap.documentdb.mongo_client_from_env", return_value=client):
        result = documentdb_health()
    assert result["status"] == "ok"
    client.close.assert_called_once()
