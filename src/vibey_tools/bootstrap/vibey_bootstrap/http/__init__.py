"""Hardened outbound HTTP client — sync requests stack."""

from __future__ import annotations

import logging
import re
import tempfile
from typing import Any

from vibey_bootstrap.http._common import DEFAULT_TIMEOUT, check_ssrf, inject_traceparent

_logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = DEFAULT_TIMEOUT


def build_session(
    *,
    total_retries: int = 5,
    backoff_factor: float = 1.0,
    pool_connections: int = 10,
    pool_maxsize: int = 10,
) -> Any:
    """Return a ``requests.Session`` with urllib3 Retry mounted."""
    import requests  # type: ignore[import-untyped]
    from requests.adapters import HTTPAdapter  # type: ignore[import-untyped]
    from urllib3.util.retry import Retry

    retry = Retry(
        total=total_retries,
        backoff_factor=backoff_factor,
        backoff_jitter=0.3,
        status_forcelist=(408, 429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"]),
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    session = requests.Session()
    adapter = HTTPAdapter(
        max_retries=retry,
        pool_connections=pool_connections,
        pool_maxsize=pool_maxsize,
    )
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def request_with_retry(
    method: str,
    url: str,
    *,
    session: Any | None = None,
    timeout: float = _DEFAULT_TIMEOUT,
    headers: dict[str, str] | None = None,
    allow_private: bool = False,
    **kwargs: Any,
) -> Any:
    """Issue an HTTP request with default timeout, traceparent, and SSRF guard."""
    check_ssrf(url, allow_private=allow_private)
    sess = session or build_session()
    hdrs = inject_traceparent(headers)
    return sess.request(method.upper(), url, headers=hdrs, timeout=timeout, **kwargs)


def normalize_pem(pem: str) -> str:
    """Normalize PEM strings mangled by env/Key Vault (spaces, CRLF)."""
    text = pem.strip().replace("\\n", "\n")
    if "BEGIN" not in text:
        text = re.sub(r"\s+", "\n", text)
    return text.replace("\r\n", "\n")


def write_temp_pem(pem: str, *, suffix: str = ".pem") -> str:
    """Write normalized PEM to a temp file; caller owns cleanup."""
    path = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False)
    path.write(normalize_pem(pem))
    path.close()
    return path.name


__all__ = ["build_session", "normalize_pem", "request_with_retry", "write_temp_pem"]
