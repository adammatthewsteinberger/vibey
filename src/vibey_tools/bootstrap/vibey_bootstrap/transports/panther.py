"""Panther SIEM logging transport — buffered, background-thread HTTP shipper."""

from __future__ import annotations

import gzip
import json
import logging
from typing import Any

from vibey_bootstrap.counters import bump_counter
from vibey_bootstrap.failclose import fail_open_env, optional_env
from vibey_bootstrap.logging.correlation import CorrelationFilter, get_correlation_id
from vibey_bootstrap.logging.jsonformatter import JsonLogFormatter
from vibey_bootstrap.transports._base import ShipResult, _BufferedShipper

_COUNTER_POSTS = "panther.transport.posts"
_COUNTER_THROTTLED = "panther.transport.throttled"


class PantherHandler(_BufferedShipper):
    """Buffered handler that ships log events to a Panther SIEM HTTP Log Source."""

    _THREAD_NAME = "panther-transport"

    def __init__(
        self,
        *,
        api_host: str,
        log_source_id: str,
        log_source_token: str,
        batch_size: int = 500,
        max_batch_bytes: int = 1_000_000,
        gzip_threshold: int = 1024,
        flush_interval: float = 5.0,
        max_buffer: int = 10_000,
        timeout: float = 5.0,
    ) -> None:
        super().__init__(
            counter_prefix="panther",
            batch_size=batch_size,
            max_batch_bytes=max_batch_bytes,
            flush_interval=flush_interval,
            max_buffer=max_buffer,
        )
        self._api_host = api_host.rstrip("/")
        self._log_source_id = log_source_id
        self._log_source_token = log_source_token
        self._endpoint = f"{self._api_host}/logsources/{self._log_source_id}/events"
        self.batch_size = self._batch_size
        self.max_batch_bytes = max_batch_bytes
        self.gzip_threshold = max(0, gzip_threshold)
        self.flush_interval = flush_interval
        self.timeout = timeout

        self.setFormatter(JsonLogFormatter())
        self.addFilter(CorrelationFilter())
        self._session: Any = _build_session()

    def emit(self, record: logging.LogRecord) -> None:
        try:
            raw = self.format(record)
            try:
                event: dict[str, Any] = json.loads(raw)
            except (ValueError, TypeError):
                event = {"message": raw}
            correlation_id = get_correlation_id()
            if correlation_id and "p_correlation_id" not in event:
                event["p_correlation_id"] = correlation_id
            line = json.dumps(event, default=str)
            maxlen = self._buffer.maxlen or 0
            with self._lock:
                was_full = maxlen > 0 and len(self._buffer) >= maxlen
                self._buffer.append(line)
                current_size = len(self._buffer)
            if was_full:
                bump_counter("panther.transport.dropped")
            if current_size >= self._batch_size:
                self._flush_now.set()
        except Exception:
            self.handleError(record)

    def _on_close(self) -> None:
        try:
            self._session.close()
        except Exception:
            pass

    def _ship(self, batch: list[str]) -> ShipResult:
        events: list[dict[str, Any]] = []
        for line in batch:
            try:
                events.append(json.loads(line))
            except (ValueError, TypeError):
                events.append({"message": line})
        if not events:
            return ShipResult(ok=True, count=0)

        payload = json.dumps({"events": events}, default=str).encode("utf-8")
        headers: dict[str, str] = {
            "Authorization": f"Bearer {self._log_source_token}",
            "Content-Type": "application/json",
        }
        if len(payload) >= self.gzip_threshold:
            payload = gzip.compress(payload)
            headers["Content-Encoding"] = "gzip"

        bump_counter(_COUNTER_POSTS)
        try:
            resp = self._session.post(
                self._endpoint, data=payload, headers=headers, timeout=self.timeout
            )
        except Exception:
            return ShipResult(ok=False, count=0)

        status = getattr(resp, "status_code", 0)
        if 200 <= status < 300:
            return ShipResult(ok=True, count=len(events))
        if status == 429:
            bump_counter(_COUNTER_THROTTLED)
        return ShipResult(ok=False, count=0)


def _build_session() -> Any:
    import requests  # type: ignore[import-untyped]
    from requests.adapters import HTTPAdapter  # type: ignore[import-untyped]
    from urllib3.util.retry import Retry

    retry = Retry(
        total=5,
        backoff_factor=1.0,
        backoff_jitter=0.3,
        status_forcelist=(408, 429, 500, 502, 503, 504),
        allowed_methods=frozenset(["POST"]),
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    session = requests.Session()
    adapter = HTTPAdapter(max_retries=retry, pool_connections=2, pool_maxsize=4)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def make_panther_handler() -> logging.Handler | None:
    api_host = fail_open_env("PANTHER_API_HOST")
    source_id = fail_open_env("PANTHER_LOG_SOURCE_ID")
    source_token = fail_open_env("PANTHER_LOG_SOURCE_TOKEN")

    if not api_host or not source_id or not source_token:
        return None

    try:
        return PantherHandler(
            api_host=api_host,
            log_source_id=source_id,
            log_source_token=source_token,
            batch_size=_int_env("PANTHER_BATCH_SIZE", 500),
            max_batch_bytes=_int_env("PANTHER_MAX_BATCH_BYTES", 1_000_000),
            gzip_threshold=_int_env("PANTHER_GZIP_THRESHOLD", 1024),
            flush_interval=_float_env("PANTHER_FLUSH_INTERVAL", 5.0),
            max_buffer=_int_env("PANTHER_MAX_BUFFER", 10_000),
            timeout=_float_env("PANTHER_TIMEOUT", 5.0),
        )
    except ImportError:
        logging.getLogger(__name__).debug(
            "Panther env vars are set but the [panther] extra (requests) is not "
            "installed — Panther transport disabled.",
        )
        return None


class PantherSearchClient:
    """Minimal GraphQL client for reading/searching Panther SIEM events."""

    _SEARCH_QUERY = """
    query SearchEvents($query: String!, $limit: Int) {
      search(query: $query, limit: $limit) {
        events {
          id
          timestamp
          p_event_time
          p_correlation_id
          raw
        }
      }
    }
    """

    def __init__(self, *, api_host: str, api_key: str, timeout: float = 10.0) -> None:
        self._graphql_url = f"{api_host.rstrip('/')}/graphql/v1"
        self._api_key = api_key
        self._timeout = timeout
        self._session: Any = _build_session()

    def search(self, query: str, *, limit: int = 100) -> list[dict[str, Any]]:
        payload = json.dumps(
            {"query": self._SEARCH_QUERY, "variables": {"query": query, "limit": limit}}
        ).encode("utf-8")
        headers = {
            "X-API-Key": self._api_key,
            "Content-Type": "application/json",
        }
        try:
            resp = self._session.post(
                self._graphql_url, data=payload, headers=headers, timeout=self._timeout
            )
            status = getattr(resp, "status_code", 0)
            if status != 200:
                return []
            data = resp.json()
            events = data.get("data", {}).get("search", {}).get("events", [])
            return events if isinstance(events, list) else []
        except Exception:
            return []

    def close(self) -> None:
        try:
            self._session.close()
        except Exception:
            pass


def make_panther_search_client() -> PantherSearchClient | None:
    api_host = fail_open_env("PANTHER_API_HOST")
    api_key = fail_open_env("PANTHER_API_KEY")

    if not api_host or not api_key:
        return None

    try:
        return PantherSearchClient(
            api_host=api_host,
            api_key=api_key,
            timeout=_float_env("PANTHER_TIMEOUT", 10.0),
        )
    except ImportError:
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


__all__ = [
    "PantherHandler",
    "PantherSearchClient",
    "make_panther_handler",
    "make_panther_search_client",
]
