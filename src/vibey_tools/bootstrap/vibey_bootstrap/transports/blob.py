"""Azure Blob Storage logging transport — buffered NDJSON shipper."""

from __future__ import annotations

import logging
import socket
import threading
from datetime import UTC, datetime
from typing import Any

from vibey_bootstrap.counters import bump_counter
from vibey_bootstrap.failclose import fail_open_env, optional_env
from vibey_bootstrap.logging.correlation import CorrelationFilter
from vibey_bootstrap.logging.jsonformatter import JsonLogFormatter
from vibey_bootstrap.transports._base import ShipResult, _BufferedShipper

_COUNTER_POSTS = "blob.transport.posts"

_DEFAULT_PREFIX = "logs"
_DEFAULT_MODE = "append"
_DEFAULT_ROLL = "hour"
_DEFAULT_BATCH_SIZE = 200
_DEFAULT_FLUSH_INTERVAL = 5.0
_DEFAULT_MAX_BUFFER = 10_000


class BlobHandler(_BufferedShipper):
    """Buffered handler that ships NDJSON log records to Azure Blob Storage."""

    _THREAD_NAME = "blob-transport"

    def __init__(
        self,
        *,
        container_client: Any,
        prefix: str = _DEFAULT_PREFIX,
        mode: str = _DEFAULT_MODE,
        roll: str = _DEFAULT_ROLL,
        batch_size: int = _DEFAULT_BATCH_SIZE,
        flush_interval: float = _DEFAULT_FLUSH_INTERVAL,
        max_buffer: int = _DEFAULT_MAX_BUFFER,
    ) -> None:
        super().__init__(
            counter_prefix="blob",
            batch_size=batch_size,
            flush_interval=flush_interval,
            max_buffer=max_buffer,
        )
        self._container_client = container_client
        self._prefix = prefix.strip("/")
        self._mode = mode.lower()
        self._roll = roll.lower()
        self.batch_size = self._batch_size
        self.flush_interval = flush_interval

        self.setFormatter(JsonLogFormatter())
        self.addFilter(CorrelationFilter())

        self._current_window: str = ""
        self._append_client: Any = None
        self._blob_lock = threading.Lock()

    def _ship(self, batch: list[str]) -> ShipResult:
        if not batch:
            return ShipResult(ok=True, count=0)
        data = "\n".join(batch) + "\n"
        body = data.encode("utf-8")
        bump_counter(_COUNTER_POSTS)
        try:
            if self._mode == "block":
                self._ship_block(body)
            else:
                self._ship_append(body)
            return ShipResult(ok=True, count=len(batch))
        except Exception:
            return ShipResult(ok=False, count=0)

    def _ship_append(self, body: bytes) -> None:
        client = self._get_append_client()
        client.append_block(body, length=len(body))

    def _get_append_client(self) -> Any:
        window = self._window_key()
        with self._blob_lock:
            if window != self._current_window or self._append_client is None:
                self._current_window = window
                blob_name = self._blob_name_append(window)
                client = self._container_client.get_blob_client(blob_name)
                try:
                    client.create_append_blob()
                except Exception:
                    pass
                self._append_client = client
        return self._append_client

    def _blob_name_append(self, window: str) -> str:
        host = _safe_hostname()
        now = datetime.now(UTC)
        date_path = f"{now.year:04d}/{now.month:02d}/{now.day:02d}"
        return f"{self._prefix}/{date_path}/{host}-{window}.jsonl"

    def _window_key(self) -> str:
        now = datetime.now(UTC)
        if self._roll == "day":
            return f"{now.year:04d}{now.month:02d}{now.day:02d}"
        return f"{now.hour:02d}"

    def _ship_block(self, body: bytes) -> None:
        blob_name = self._blob_name_block()
        client = self._container_client.get_blob_client(blob_name)
        client.upload_blob(body, overwrite=False)

    def _blob_name_block(self) -> str:
        host = _safe_hostname()
        now = datetime.now(UTC)
        ts = now.strftime("%Y%m%d-%H%M%S-%f")[:-3]
        date_path = f"{now.year:04d}/{now.month:02d}/{now.day:02d}"
        return f"{self._prefix}/{date_path}/{host}-{ts}.jsonl"


def make_blob_handler() -> logging.Handler | None:
    container = fail_open_env("BLOB_LOG_CONTAINER")
    if not container:
        return None

    account_url = fail_open_env("BLOB_LOG_ACCOUNT_URL")
    conn_str = fail_open_env("BLOB_LOG_CONNECTION_STRING")
    if not account_url and not conn_str:
        return None

    try:
        container_client = _build_container_client(
            container=container,
            account_url=account_url or None,
            conn_str=conn_str or None,
        )
    except ImportError:
        logging.getLogger(__name__).debug(
            "BLOB_LOG_CONTAINER set but the [bloblog] extra (azure-storage-blob) "
            "is not installed — Blob transport disabled.",
        )
        return None
    except Exception:
        logging.getLogger(__name__).debug(
            "Blob transport: failed to build container client — transport disabled.",
            exc_info=True,
        )
        return None

    return BlobHandler(
        container_client=container_client,
        prefix=optional_env("BLOB_LOG_PREFIX") or _DEFAULT_PREFIX,
        mode=optional_env("BLOB_LOG_MODE") or _DEFAULT_MODE,
        roll=optional_env("BLOB_LOG_ROLL") or _DEFAULT_ROLL,
        batch_size=_int_env("BLOB_BATCH_SIZE", _DEFAULT_BATCH_SIZE),
        flush_interval=_float_env("BLOB_FLUSH_INTERVAL", _DEFAULT_FLUSH_INTERVAL),
        max_buffer=_int_env("BLOB_MAX_BUFFER", _DEFAULT_MAX_BUFFER),
    )


def _build_container_client(
    *,
    container: str,
    account_url: str | None,
    conn_str: str | None,
) -> Any:
    from azure.storage.blob import ContainerClient  # type: ignore[import-not-found]

    if account_url:
        from vibey_bootstrap.identity import build_credential

        credential = build_credential()
        return ContainerClient(
            account_url=account_url, container_name=container, credential=credential
        )

    if conn_str:
        return ContainerClient.from_connection_string(conn_str=conn_str, container_name=container)

    raise ValueError("Either account_url or conn_str must be provided")


def _safe_hostname() -> str:
    try:
        raw = socket.gethostname() or "host"
    except Exception:
        raw = "host"
    safe = "".join(c if c.isalnum() or c == "-" else "-" for c in raw.lower())
    return safe[:40].strip("-") or "host"


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


__all__ = ["BlobHandler", "make_blob_handler"]
