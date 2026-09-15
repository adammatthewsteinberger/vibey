"""Sumo Logic logging transport — buffered, background-thread HTTP shipper."""

from __future__ import annotations

import gzip
import logging
from collections.abc import Mapping
from typing import Any

from vibey_bootstrap.counters import bump_counter
from vibey_bootstrap.failclose import fail_open_env, optional_env
from vibey_bootstrap.logging.correlation import CorrelationFilter
from vibey_bootstrap.logging.jsonformatter import JsonLogFormatter
from vibey_bootstrap.transports._base import ShipResult, _BufferedShipper

_COUNTER_POSTS = "sumologic.transport.posts"
_COUNTER_THROTTLED = "sumologic.transport.throttled"


class SumoLogicHandler(_BufferedShipper):
    """Buffered handler that ships log lines to a Sumo Logic HTTP Source."""

    _THREAD_NAME = "sumologic-transport"

    def __init__(
        self,
        *,
        endpoint_url: str,
        source_category: str | None = None,
        source_host: str | None = None,
        source_name: str = "vibey-bootstrap",
        source_token: str | None = None,
        fields: Mapping[str, str] | None = None,
        batch_size: int = 100,
        max_batch_bytes: int = 1_000_000,
        gzip_threshold: int = 1024,
        flush_interval: float = 5.0,
        max_buffer: int = 10_000,
        timeout: float = 5.0,
    ) -> None:
        super().__init__(
            counter_prefix="sumologic",
            batch_size=batch_size,
            max_batch_bytes=max_batch_bytes,
            flush_interval=flush_interval,
            max_buffer=max_buffer,
        )
        self.endpoint_url = endpoint_url
        self.source_category = source_category
        self.source_host = source_host
        self.source_name = source_name
        self.source_token = source_token
        self.fields = dict(fields) if fields else {}
        self.batch_size = self._batch_size
        self.max_batch_bytes = max_batch_bytes
        self.gzip_threshold = max(0, gzip_threshold)
        self.flush_interval = flush_interval
        self.timeout = timeout

        self.setFormatter(JsonLogFormatter())
        self.addFilter(CorrelationFilter())
        self._session: Any = _build_session()

    def _on_close(self) -> None:
        try:
            self._session.close()
        except Exception:
            pass

    def _ship(self, batch: list[str]) -> ShipResult:
        if not batch:
            return ShipResult(ok=True, count=0)

        body = "\n".join(batch).encode("utf-8")
        headers = {"Content-Type": "application/json", "X-Sumo-Name": self.source_name}
        if self.source_category:
            headers["X-Sumo-Category"] = self.source_category
        if self.source_host:
            headers["X-Sumo-Host"] = self.source_host
        if self.source_token:
            headers["x-sumo-token"] = self.source_token
        if self.fields:
            headers["X-Sumo-Fields"] = ",".join(f"{k}={v}" for k, v in self.fields.items())
        if len(body) >= self.gzip_threshold:
            body = gzip.compress(body)
            headers["Content-Encoding"] = "gzip"

        bump_counter(_COUNTER_POSTS)
        try:
            resp = self._session.post(
                self.endpoint_url, data=body, headers=headers, timeout=self.timeout
            )
        except Exception:
            return ShipResult(ok=False, count=0)

        status = getattr(resp, "status_code", 0)
        if 200 <= status < 300:
            return ShipResult(ok=True, count=len(batch))
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


def make_sumo_logic_handler() -> logging.Handler | None:
    endpoint = fail_open_env("SUMO_LOGIC_COLLECTOR_URL")
    if not endpoint:
        return None

    try:
        return SumoLogicHandler(
            endpoint_url=endpoint,
            source_category=optional_env("SUMO_LOGIC_SOURCE_CATEGORY") or None,
            source_host=optional_env("SUMO_LOGIC_SOURCE_HOST") or None,
            source_token=optional_env("SUMO_LOGIC_COLLECTOR_TOKEN") or None,
            fields=_parse_fields(optional_env("SUMO_LOGIC_FIELDS")),
            batch_size=_int_env("SUMO_LOGIC_BATCH_SIZE", 100),
            max_batch_bytes=_int_env("SUMO_LOGIC_MAX_BATCH_BYTES", 1_000_000),
            gzip_threshold=_int_env("SUMO_LOGIC_GZIP_THRESHOLD", 1024),
            flush_interval=_float_env("SUMO_LOGIC_FLUSH_INTERVAL", 5.0),
            max_buffer=_int_env("SUMO_LOGIC_MAX_BUFFER", 10_000),
            timeout=_float_env("SUMO_LOGIC_TIMEOUT", 5.0),
        )
    except ImportError:
        logging.getLogger(__name__).debug(
            "SUMO_LOGIC_COLLECTOR_URL set but the [sumologic] extra (requests) "
            "is not installed — Sumo Logic transport disabled.",
        )
        return None


def _parse_fields(raw: str | None) -> dict[str, str]:
    if not raw:
        return {}
    out: dict[str, str] = {}
    for pair in raw.split(","):
        key, sep, value = pair.partition("=")
        key = key.strip()
        if sep and key:
            out[key] = value.strip()
    return out


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


__all__ = ["SumoLogicHandler", "make_sumo_logic_handler"]
