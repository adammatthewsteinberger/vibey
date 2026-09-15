"""Azure Data Explorer (Kusto) logging transport — streaming NDJSON ingest."""

from __future__ import annotations

import io
import logging
from typing import Any

from vibey_bootstrap.counters import bump_counter
from vibey_bootstrap.failclose import fail_open_env, optional_env
from vibey_bootstrap.logging.correlation import CorrelationFilter
from vibey_bootstrap.logging.jsonformatter import JsonLogFormatter
from vibey_bootstrap.transports._base import ShipResult, _BufferedShipper

_COUNTER_FLUSHES = "adx.transport.flushes"


class AdxHandler(_BufferedShipper):
    """Buffered handler streaming NDJSON to ADX via streaming ingestion."""

    _THREAD_NAME = "adx-transport"

    def __init__(
        self,
        *,
        cluster_uri: str,
        database: str,
        table: str = "Logs",
        credential: Any = None,
        batch_size: int = 200,
        flush_interval: float = 5.0,
        max_buffer: int = 10_000,
    ) -> None:
        super().__init__(
            counter_prefix="adx",
            batch_size=batch_size,
            flush_interval=flush_interval,
            max_buffer=max_buffer,
        )
        self._cluster_uri = cluster_uri
        self._database = database
        self._table = table
        self._credential = credential
        self._client: Any = None

        self.setFormatter(JsonLogFormatter())
        self.addFilter(CorrelationFilter())

    def _get_client(self) -> Any:
        if self._client is None:
            from azure.kusto.data import KustoConnectionStringBuilder
            from azure.kusto.ingest import KustoStreamingIngestClient

            if self._credential is not None:
                kcsb = KustoConnectionStringBuilder.with_azure_token_credential(
                    self._cluster_uri, self._credential
                )
            else:
                from vibey_bootstrap.identity import build_credential

                kcsb = KustoConnectionStringBuilder.with_azure_token_credential(
                    self._cluster_uri, build_credential()
                )
            self._client = KustoStreamingIngestClient(kcsb)
        return self._client

    def _ship(self, batch: list[str]) -> ShipResult:
        if not batch:
            return ShipResult(ok=True, count=0)
        bump_counter(_COUNTER_FLUSHES)
        try:
            from azure.kusto.data.data_format import DataFormat
            from azure.kusto.ingest import IngestionProperties

            payload = "\n".join(batch)
            props = IngestionProperties(
                database=self._database,
                table=self._table,
                data_format=DataFormat.MULTIJSON,
            )
            self._get_client().ingest_from_stream(io.StringIO(payload), ingestion_properties=props)
            return ShipResult(ok=True, count=len(batch))
        except Exception:
            return ShipResult(ok=False, count=0)


def make_adx_handler() -> logging.Handler | None:
    cluster_uri = fail_open_env("ADX_CLUSTER_URI")
    database = fail_open_env("ADX_DATABASE")
    if not cluster_uri or not database:
        return None
    table = optional_env("ADX_TABLE") or "Logs"
    try:
        return AdxHandler(
            cluster_uri=cluster_uri,
            database=database,
            table=table,
            batch_size=_int_env("ADX_BATCH_SIZE", 200),
            flush_interval=_float_env("ADX_FLUSH_INTERVAL", 5.0),
            max_buffer=_int_env("ADX_MAX_BUFFER", 10_000),
        )
    except ImportError:
        logging.getLogger(__name__).debug(
            "ADX env set but [adxlog] extra not installed — ADX transport disabled."
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


__all__ = ["AdxHandler", "make_adx_handler"]
