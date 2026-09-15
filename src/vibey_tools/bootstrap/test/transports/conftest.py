"""Shared fixtures for transport tests.

Each test starts from a clean registry + root-logger state and a clean set of
transport env vars, then restores everything afterward. ``AZURE_BOOTSTRAP_ALLOW_RESET``
is set globally by the top-level ``test/conftest.py``.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Iterator

import pytest

import vibey_bootstrap.transports as transports
from vibey_bootstrap.counters import _reset_counters

_TRANSPORT_ENV = (
    "CONSOLE_LOGGING_ENABLED",
    "APP_INSIGHTS_LOGGING_ENABLED",
    "SUMO_LOGIC_LOGGING_ENABLED",
    "SUMO_LOGIC_COLLECTOR_URL",
    "SUMO_LOGIC_SOURCE_CATEGORY",
    "SUMO_LOGIC_SOURCE_HOST",
    "SUMO_LOGIC_BATCH_SIZE",
    "SUMO_LOGIC_FLUSH_INTERVAL",
    "SUMO_LOGIC_MAX_BUFFER",
    "SUMO_LOGIC_TIMEOUT",
    "PANTHER_LOGGING_ENABLED",
    "PANTHER_API_HOST",
    "PANTHER_LOG_SOURCE_ID",
    "PANTHER_LOG_SOURCE_TOKEN",
    "FILE_LOGGING_ENABLED",
    "FILE_LOG_PATH",
    "BLOB_LOGGING_ENABLED",
    "BLOB_LOG_CONTAINER",
    "BLOB_LOG_ACCOUNT_URL",
    "SQL_LOGGING_ENABLED",
    "SQL_LOG_DSN",
    "NOSQL_LOGGING_ENABLED",
    "NOSQL_LOG_URI",
    "NOSQL_LOG_DATABASE",
    "ADX_LOGGING_ENABLED",
    "ADX_CLUSTER_URI",
    "EVENTHUBS_LOGGING_ENABLED",
    "EVENTHUB_FQNS",
    "EVENTHUB_NAME",
)


@pytest.fixture(autouse=True)
def _clean_state() -> Iterator[None]:
    saved_env = {k: os.environ.get(k) for k in _TRANSPORT_ENV}
    for k in _TRANSPORT_ENV:
        os.environ.pop(k, None)
    root = logging.getLogger()
    saved_handlers = list(root.handlers)

    transports._reset_transports()
    _reset_counters()
    try:
        yield
    finally:
        transports._reset_transports()
        root.handlers[:] = saved_handlers
        for k, v in saved_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
