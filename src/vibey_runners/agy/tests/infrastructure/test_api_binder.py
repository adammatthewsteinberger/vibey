# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agyloop.infrastructure.api.binder import build_api_app, kebab
from agyloop.infrastructure.api.discover import (
    parse_api_lane,
)
from agyloop.infrastructure.api.gateway import (
    GeminiRestGateway,
    UrllibTransport,
    _load_json_payload,
    _method_for,
    _vertex_access_token,
    default_gateway,
    interpolate_path,
)

runner = CliRunner()


def test_kebab() -> None:
    assert kebab("generateContent") == "generate-content"
    assert kebab("list") == "list"
    assert kebab("get_model") == "get-model"


def test_parse_api_lane() -> None:
    assert parse_api_lane("developer") == "developer"
    assert parse_api_lane("VERTEX") == "vertex"
    with pytest.raises(ValueError, match="unknown API lane"):
        parse_api_lane("invalid")


def test_interpolate_path_missing_param() -> None:
    with pytest.raises(ValueError, match="missing path parameter"):
        interpolate_path("v1beta/{+name}:cancel", {})


def test_load_json_payload(tmp_path: Path) -> None:
    # Both json and json_file -> ValueError
    f = tmp_path / "payload.json"
    f.write_text('{"a": 1}', encoding="utf-8")
    with pytest.raises(ValueError, match="pass only one"):
        _load_json_payload(json_body="{}", json_file=f)

    # Empty
    assert _load_json_payload(json_body=None, json_file=None) == {}

    # File loading
    assert _load_json_payload(json_body=None, json_file=f) == {"a": 1}

    # Non-dict json
    with pytest.raises(ValueError, match="must be a JSON object"):
        _load_json_payload(json_body="[1, 2, 3]", json_file=None)


def test_urllib_transport() -> None:
    transport = UrllibTransport()
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b'{"status": "ok"}'
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        status, text = transport.request(
            "GET", "https://generativelanguage.googleapis.com", headers={}, body=None
        )
        assert status == 200
        assert text == '{"status": "ok"}'

    # HTTPError
    import urllib.error

    with patch(
        "urllib.request.urlopen",
        side_effect=urllib.error.HTTPError(
            "url", 404, "not found", {}, MagicMock(read=lambda: b"not found")
        ),
    ):
        status, text = transport.request(
            "GET", "https://generativelanguage.googleapis.com", headers={}, body=None
        )
        assert status == 404
        assert text == "not found"


def test_api_gateway_errors_and_methods(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Unknown method

    with pytest.raises(ValueError, match="unknown method"):
        _method_for("unknown.nonexistentMethod", "developer")

    # Vertex access token missing
    monkeypatch.delenv("GOOGLE_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("CLOUDSDK_AUTH_ACCESS_TOKEN", raising=False)
    with pytest.raises(ValueError, match="Vertex lane needs GOOGLE_ACCESS_TOKEN"):
        _vertex_access_token()

    # Vertex access token from CLOUDSDK_AUTH_ACCESS_TOKEN
    monkeypatch.setenv("CLOUDSDK_AUTH_ACCESS_TOKEN", "token123")
    assert _vertex_access_token() == "token123"

    # Gateway invoke with GET (leftover query params)
    monkeypatch.setenv("GOOGLE_API_KEY", "key123")
    mock_transport = MagicMock()
    mock_transport.request.return_value = (200, '{"models": []}')
    gw = GeminiRestGateway(transport=mock_transport)
    res = gw.invoke("models.list", scalar_values={"pageSize": 10})
    assert res == {"models": []}

    # Gateway invoke with failed status (400)
    mock_transport.request.return_value = (400, "bad request")
    with pytest.raises(ValueError, match="failed \\(400\\)"):
        gw.invoke("models.list")

    # Gateway invoke with non-json response (status 200)
    mock_transport.request.return_value = (200, "plain text")
    res = gw.invoke("models.list")
    assert res == {"raw": "plain text"}

    # Default gateway
    assert isinstance(default_gateway(), GeminiRestGateway)


def test_api_cli_app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "key123")
    mock_gw = MagicMock()
    mock_gw.invoke_and_print.return_value = '{"model": "gemini-2.5-flash"}'

    app = build_api_app(gateway=mock_gw)

    # Invalid lane option
    res = runner.invoke(
        app, ["--lane", "badlane", "models", "get", "--json", '{"name": "models/m"}']
    )
    assert res.exit_code == 1

    # Valid execution
    res = runner.invoke(
        app, ["--lane", "developer", "models", "get", "--json", '{"name": "models/m"}']
    )
    assert res.exit_code == 0
    assert "gemini-2.5-flash" in res.output

    # Lane mismatch error
    res = runner.invoke(
        app, ["--lane", "vertex", "models", "get", "--json", '{"name": "models/m"}']
    )
    assert res.exit_code == 1
    assert "belongs to --lane developer" in res.output

    # Gateway invocation exception
    mock_gw.invoke_and_print.side_effect = ValueError("invoke failed")
    res = runner.invoke(
        app, ["--lane", "developer", "models", "get", "--json", '{"name": "models/m"}']
    )
    assert res.exit_code == 1
    assert "invoke failed" in res.output
