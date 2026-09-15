"""MongoDB / Cosmos DB document database access."""

from __future__ import annotations

import logging
import time
from typing import Any

from vibey_bootstrap.failclose import fail_open_env, require_env

_logger = logging.getLogger(__name__)


def mongo_client_from_env(*, uri_env: str = "NOSQL_URI") -> Any:
    """Build a pymongo ``MongoClient`` from env."""
    import pymongo  # type: ignore[import-untyped]

    uri = require_env(uri_env)
    return pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)


def documentdb_health(
    *, uri_env: str = "NOSQL_URI", database_env: str = "NOSQL_DATABASE"
) -> dict[str, Any]:
    """Return ``{status, latency_ms}`` for health probes."""
    start = time.perf_counter()
    try:
        client = mongo_client_from_env(uri_env=uri_env)
        db_name = fail_open_env(database_env) or "admin"
        client[db_name].command("ping")
        latency = (time.perf_counter() - start) * 1000
        client.close()
        return {"status": "ok", "latency_ms": round(latency, 2)}
    except Exception as exc:
        return {"status": "error", "latency_ms": None, "error": str(exc)}


__all__ = ["documentdb_health", "mongo_client_from_env"]
