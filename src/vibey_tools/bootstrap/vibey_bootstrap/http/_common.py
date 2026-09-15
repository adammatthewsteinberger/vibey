"""Shared HTTP helpers for sync and async clients."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

from vibey_bootstrap.logging.correlation import get_correlation_id

DEFAULT_TIMEOUT = 30.0
_BLOCKED_HOSTS = frozenset({"169.254.169.254", "metadata.google.internal"})


def inject_traceparent(headers: dict[str, str] | None) -> dict[str, str]:
    out = dict(headers or {})
    cid = get_correlation_id()
    if cid and "traceparent" not in out:
        out["traceparent"] = f"00-{cid.replace('-', '')[:32]}-{'0' * 16}-01"
    return out


def check_ssrf(url: str, *, allow_private: bool = False) -> None:
    parsed = urlparse(url)
    host = parsed.hostname or ""
    if host in _BLOCKED_HOSTS:
        raise ValueError(f"SSRF blocked: {host}")
    if allow_private:
        return
    try:
        for info in socket.getaddrinfo(host, None):
            addr = info[4][0]
            ip = ipaddress.ip_address(addr)
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                raise ValueError(f"SSRF blocked private address: {addr}")
    except socket.gaierror:
        pass
