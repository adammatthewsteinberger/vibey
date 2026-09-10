# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Localhost Gemini rewrite proxy — withdrawn model id only, no live Google."""

from __future__ import annotations

import urllib.request
from unittest.mock import MagicMock, patch

import pytest

from agyloop.domain.classify import WITHDRAWN_INPUT_DETECTION_MODEL
from agyloop.domain.model_profile import INPUT_DETECTION_MODEL
from agyloop.infrastructure.agent.gemini_rewrite import (
    GeminiRewriteProxy,
    _forward_http,
    rewrite_proxy_disabled,
    rewrite_withdrawn_model_bytes,
    rewrite_withdrawn_model_text,
    should_install_rewrite_ca,
)


def test_rewrite_withdrawn_model_in_path_and_body() -> None:
    path = f"/v1beta/models/{WITHDRAWN_INPUT_DETECTION_MODEL}:generateContent"
    assert INPUT_DETECTION_MODEL in rewrite_withdrawn_model_text(path)
    assert WITHDRAWN_INPUT_DETECTION_MODEL not in rewrite_withdrawn_model_text(path)
    body = f'{{"model":"{WITHDRAWN_INPUT_DETECTION_MODEL}"}}'.encode()
    rewritten = rewrite_withdrawn_model_bytes(body)
    assert INPUT_DETECTION_MODEL.encode() in rewritten
    assert WITHDRAWN_INPUT_DETECTION_MODEL.encode() not in rewritten


def test_proxy_refuses_non_loopback() -> None:
    with pytest.raises(ValueError, match="loopback"):
        GeminiRewriteProxy(listen_host="0.0.0.0")


def test_proxy_url_not_running() -> None:
    proxy = GeminiRewriteProxy()
    with pytest.raises(RuntimeError, match="not running"):
        _ = proxy.url


def test_rewrite_proxy_methods_and_query_string() -> None:
    seen: list[tuple[str, str, bytes]] = []

    def transport(
        method: str, path: str, body: bytes, headers: dict[str, str]
    ) -> tuple[int, bytes, dict[str, str]]:
        del headers
        seen.append((method, path, body))
        return (
            200,
            b'{"ok":true}',
            {
                "Content-Type": "application/json",
                "Transfer-Encoding": "chunked",
                "Connection": "keep-alive",
            },
        )

    proxy = GeminiRewriteProxy(listen_host="127.0.0.1", transport=transport)
    url = proxy.start()
    try:
        # GET with query parameter
        req_get = urllib.request.Request(
            f"{url}/v1beta/models/{WITHDRAWN_INPUT_DETECTION_MODEL}?key=123&m={WITHDRAWN_INPUT_DETECTION_MODEL}",
            method="GET",
        )
        with urllib.request.urlopen(req_get, timeout=5) as response:
            assert response.status == 200

        # POST
        req_post = urllib.request.Request(
            f"{url}/v1beta/models/{WITHDRAWN_INPUT_DETECTION_MODEL}:generateContent",
            data=b'{"contents":[]}',
            method="POST",
        )
        with urllib.request.urlopen(req_post, timeout=5) as response:
            assert response.status == 200

        # PUT
        req_put = urllib.request.Request(f"{url}/v1beta/item", data=b"{}", method="PUT")
        with urllib.request.urlopen(req_put, timeout=5) as response:
            assert response.status == 200

        # PATCH
        req_patch = urllib.request.Request(f"{url}/v1beta/item", data=b"{}", method="PATCH")
        with urllib.request.urlopen(req_patch, timeout=5) as response:
            assert response.status == 200

        # DELETE
        req_del = urllib.request.Request(f"{url}/v1beta/item", method="DELETE")
        with urllib.request.urlopen(req_del, timeout=5) as response:
            assert response.status == 200

        # CONNECT (returns 501 error)
        import http.client

        conn = http.client.HTTPConnection("127.0.0.1", int(url.split(":")[-1]), timeout=5)
        conn.request("CONNECT", "example.com:443")
        resp = conn.getresponse()
        assert resp.status == 501
        conn.close()
    finally:
        proxy.stop()

    assert any(
        m == "GET" and "key=123" in p and WITHDRAWN_INPUT_DETECTION_MODEL not in p
        for m, p, _ in seen
    )
    assert any(m == "POST" and WITHDRAWN_INPUT_DETECTION_MODEL not in p for m, p, _ in seen)


def test_rewrite_proxy_with_default_forward_handler() -> None:
    proxy = GeminiRewriteProxy(
        listen_host="127.0.0.1", origin_host="127.0.0.1", origin_port=1, origin_tls=False
    )
    with patch(
        "agyloop.infrastructure.agent.gemini_rewrite._forward_http",
        return_value=(200, b'{"forwarded":true}', {"X-Fwd": "1"}),
    ):
        url = proxy.start()
        try:
            req = urllib.request.Request(f"{url}/test", method="GET")
            with urllib.request.urlopen(req, timeout=5) as response:
                assert response.status == 200
                assert response.read() == b'{"forwarded":true}'
        finally:
            proxy.stop()


def test_forward_http_tls_and_plain() -> None:
    # Test _forward_http with mock http / https connection
    with patch("http.client.HTTPSConnection") as mock_https:
        mock_conn = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b"response data"
        mock_resp.getheaders.return_value = [("X-Test", "1")]
        mock_conn.getresponse.return_value = mock_resp
        mock_https.return_value = mock_conn

        status, payload, headers = _forward_http(
            host="generativelanguage.googleapis.com",
            port=443,
            tls=True,
            method="POST",
            path="/path",
            body=b"body",
            headers={"H": "V"},
        )
        assert status == 200
        assert payload == b"response data"
        assert headers["X-Test"] == "1"

    with patch("agyloop.infrastructure.agent.gemini_rewrite.HTTPConnection") as mock_http:
        mock_conn = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b"plain data"
        mock_resp.getheaders.return_value = []
        mock_conn.getresponse.return_value = mock_resp
        mock_http.return_value = mock_conn

        status, payload, headers = _forward_http(
            host="localhost",
            port=8080,
            tls=False,
            method="GET",
            path="/path",
            body=b"",
            headers={},
        )
        assert status == 200
        assert payload == b"plain data"


def test_rewrite_proxy_disabled_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AGYLOOP_GEMINI_REWRITE_PROXY", raising=False)
    assert rewrite_proxy_disabled() is False
    monkeypatch.setenv("AGYLOOP_GEMINI_REWRITE_PROXY", "0")
    assert rewrite_proxy_disabled() is True


def test_rewrite_ca_install_is_opt_in(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AGYLOOP_INSTALL_REWRITE_CA", raising=False)
    assert should_install_rewrite_ca() is False
    monkeypatch.setenv("AGYLOOP_INSTALL_REWRITE_CA", "1")
    assert should_install_rewrite_ca() is True
