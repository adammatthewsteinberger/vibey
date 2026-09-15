# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Localhost-only reverse proxy that rewrites withdrawn Gemini model ids.

Listens on loopback. Rewrites only ``gemini-2.5-flash-lite`` in request paths
and bodies. Does not log API keys. Off unless earlier retarget layers failed.
Does not install a system-wide CA unless ``AGYLOOP_INSTALL_REWRITE_CA=1``.
"""

from __future__ import annotations

import logging
import os
import socket
import threading
from collections.abc import Callable
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

from agyloop.domain.classify import WITHDRAWN_INPUT_DETECTION_MODEL
from agyloop.domain.model_profile import INPUT_DETECTION_MODEL

_LOG = logging.getLogger(__name__)

_Forward = Callable[[str, str, bytes, dict[str, str]], tuple[int, bytes, dict[str, str]]]

_WITHDRAWN = WITHDRAWN_INPUT_DETECTION_MODEL.encode("ascii")
_LIVE = INPUT_DETECTION_MODEL.encode("ascii")


def rewrite_withdrawn_model_bytes(payload: bytes) -> bytes:
    """Replace the withdrawn flash-lite id in paths or JSON bodies."""
    return payload.replace(_WITHDRAWN, _LIVE)


def rewrite_withdrawn_model_text(payload: str) -> str:
    return payload.replace(WITHDRAWN_INPUT_DETECTION_MODEL, INPUT_DETECTION_MODEL)


class GeminiRewriteProxy:
    """Loopback HTTP reverse proxy. Origin is the real Gemini host by default."""

    def __init__(
        self,
        *,
        origin_host: str = "generativelanguage.googleapis.com",
        origin_port: int = 443,
        origin_tls: bool = True,
        listen_host: str = "127.0.0.1",
        listen_port: int = 0,
        transport: _Forward | None = None,
    ) -> None:
        if listen_host not in {"127.0.0.1", "::1", "localhost"}:
            raise ValueError("rewrite proxy must listen on loopback only")
        self._origin_host = origin_host
        self._origin_port = origin_port
        self._origin_tls = origin_tls
        self._listen_host = listen_host
        self._listen_port = listen_port
        self._transport = transport
        self._httpd: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def url(self) -> str:
        if self._httpd is None:
            raise RuntimeError("rewrite proxy is not running")
        host_raw, port = self._httpd.server_address[:2]
        host = host_raw.decode() if isinstance(host_raw, (bytes, bytearray)) else str(host_raw)
        return f"http://{host}:{port}"

    def start(self) -> str:
        proxy = self

        class _Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, fmt: str, *args: object) -> None:
                del fmt, args

            def _read_body(self) -> bytes:
                length = int(self.headers.get("Content-Length", "0") or "0")
                if length <= 0:
                    return b""
                return self.rfile.read(length)

            def _forward(self, method: str) -> None:
                raw_path = self.path
                parsed = urlsplit(raw_path)
                path = rewrite_withdrawn_model_text(parsed.path or raw_path)
                if parsed.query:
                    path = f"{path}?{rewrite_withdrawn_model_text(parsed.query)}"
                body = rewrite_withdrawn_model_bytes(self._read_body())
                headers = {
                    key: value
                    for key, value in self.headers.items()
                    if key.lower() not in {"host", "proxy-connection", "content-length"}
                }
                if proxy._transport is not None:
                    status, payload, resp_headers = proxy._transport(method, path, body, headers)
                else:
                    status, payload, resp_headers = _forward_http(
                        host=proxy._origin_host,
                        port=proxy._origin_port,
                        tls=proxy._origin_tls,
                        method=method,
                        path=path,
                        body=body,
                        headers=headers,
                    )
                self.send_response(status)
                for key, value in resp_headers.items():
                    if key.lower() in {"transfer-encoding", "connection"}:
                        continue
                    self.send_header(key, value)
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def do_GET(self) -> None:  # noqa: N802
                self._forward("GET")

            def do_POST(self) -> None:  # noqa: N802
                self._forward("POST")

            def do_PUT(self) -> None:  # noqa: N802
                self._forward("PUT")

            def do_PATCH(self) -> None:  # noqa: N802
                self._forward("PATCH")

            def do_DELETE(self) -> None:  # noqa: N802
                self._forward("DELETE")

            def do_CONNECT(self) -> None:  # noqa: N802
                # Tunnel only. HTTPS MITM would require a CA in the harness
                # trust store. We never install a system CA here.
                self.send_error(501, "CONNECT rewrite requires an explicit local CA")

        httpd = ThreadingHTTPServer((self._listen_host, self._listen_port), _Handler)
        sock = httpd.socket
        if isinstance(sock, socket.socket):
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._httpd = httpd
        thread = threading.Thread(
            target=httpd.serve_forever,
            name="agyloop-gemini-rewrite",
            daemon=True,
        )
        self._thread = thread
        thread.start()
        _LOG.info("gemini.rewrite_proxy.started", extra={"url": self.url})
        return self.url

    def stop(self) -> None:
        if self._httpd is not None:
            self._httpd.shutdown()
            self._httpd.server_close()
            self._httpd = None
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None


def _forward_http(
    *,
    host: str,
    port: int,
    tls: bool,
    method: str,
    path: str,
    body: bytes,
    headers: dict[str, str],
) -> tuple[int, bytes, dict[str, str]]:
    conn: HTTPConnection
    if tls:
        import http.client

        conn = http.client.HTTPSConnection(host, port, timeout=60)
    else:
        conn = HTTPConnection(host, port, timeout=60)
    try:
        conn.request(method, path, body=body, headers=headers)
        response = conn.getresponse()
        payload = response.read()
        resp_headers = dict(response.getheaders())
        return response.status, payload, resp_headers
    finally:
        conn.close()


def rewrite_proxy_disabled() -> bool:
    return os.environ.get("AGYLOOP_GEMINI_REWRITE_PROXY", "1") == "0"


def should_install_rewrite_ca() -> bool:
    """System/user trust-store install is opt-in only. Never silent."""
    return os.environ.get("AGYLOOP_INSTALL_REWRITE_CA") == "1"
