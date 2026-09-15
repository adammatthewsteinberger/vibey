"""HTTP client tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from vibey_bootstrap.http import normalize_pem, request_with_retry


def test_normalize_pem_fixes_escaped_newlines() -> None:
    pem = "-----BEGIN CERT-----\\nABC\\n-----END CERT-----"
    assert "\\n" not in normalize_pem(pem)


def test_request_with_retry_calls_session() -> None:
    session = MagicMock()
    session.request.return_value = MagicMock(status_code=200)
    with patch("vibey_bootstrap.http.check_ssrf"):
        request_with_retry("GET", "https://example.com", session=session)
    session.request.assert_called_once()
