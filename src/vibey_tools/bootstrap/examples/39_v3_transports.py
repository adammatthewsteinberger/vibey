"""Example 39 — v3 logging transports (panther, file, blob, sql, nosql)."""

from __future__ import annotations

import logging
import os

from vibey_bootstrap import configure_transports

# Enable transports via env flags or explicit kwargs.
# Each transport soft no-ops when unconfigured or missing its pip extra.
configure_transports(
    console=True,
    panther=os.getenv("PANTHER_LOGGING_ENABLED") == "1",
    file=os.getenv("FILE_LOGGING_ENABLED") == "1",
    blob=os.getenv("BLOB_LOGGING_ENABLED") == "1",
    sql=os.getenv("SQL_LOGGING_ENABLED") == "1",
    nosql=os.getenv("NOSQL_LOGGING_ENABLED") == "1",
    adx=os.getenv("ADX_LOGGING_ENABLED") == "1",
    event_hubs=os.getenv("EVENTHUBS_LOGGING_ENABLED") == "1",
)

log = logging.getLogger("example39")
log.info("v3 transport example", extra={"component": "examples"})
