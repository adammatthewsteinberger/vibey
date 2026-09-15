# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Every capability is executable through MCP, API, CLI, SDK, and webhook contracts."""

from __future__ import annotations

import hashlib
import hmac
import json

import pytest

from vibey_gh import surfaces
from vibey_gh.cli import main


def _result(capability: str, arguments: list[str]) -> surfaces.Result:
    return surfaces.Result(capability, 0, json.dumps(arguments), "")


def test_registry_has_complete_five_surface_parity():
    matrix = surfaces.parity()
    assert set(matrix) == set(surfaces.CAPABILITIES)
    assert all(value == surfaces.SURFACES for value in matrix.values())


def test_sdk_invokes_real_cli_and_validates(monkeypatch):
    monkeypatch.setattr("vibey_gh.cli.main", lambda argv: (print(" ".join(argv)), 7)[1])
    result = surfaces.invoke("version", ["--explain"])
    assert result.exit_code == 7 and "version --explain" in result.stdout
    with pytest.raises(ValueError, match="unknown"):
        surfaces.invoke("missing")
    with pytest.raises(TypeError, match="strings"):
        surfaces.invoke("version", [1])  # type: ignore[list-item]


def test_sdk_captures_argparse_system_exit():
    result = surfaces.invoke("version", ["--not-real"])
    assert result.exit_code == 2 and "unrecognized arguments" in result.stderr


def test_api_lists_and_invokes_all_capabilities(monkeypatch):
    monkeypatch.setattr(surfaces, "invoke", _result)
    status, listing = surfaces.api_dispatch("GET", "/v1/capabilities")
    assert status == 200 and set(listing["capabilities"]) == set(surfaces.CAPABILITIES)
    for capability in surfaces.CAPABILITIES:
        status, payload = surfaces.api_dispatch(
            "POST", f"/v1/capabilities/{capability}", b'{"arguments":["--help"]}'
        )
        assert status == 200 and payload["capability"] == capability
    assert surfaces.api_dispatch("GET", "/missing")[0] == 404
    assert surfaces.api_dispatch("POST", "/v1/capabilities/version", b"{")[0] == 400
    assert surfaces.api_dispatch("POST", "/v1/capabilities/version", b'{"arguments":1}')[0] == 400
    assert surfaces.api_dispatch("POST", "/v1/capabilities/nope")[0] == 400


def test_mcp_protocol_lists_and_invokes_all_capabilities(monkeypatch):
    monkeypatch.setattr(surfaces, "invoke", _result)
    initialized = surfaces.mcp_dispatch({"id": 1, "method": "initialize"})
    assert initialized["result"]["serverInfo"]["name"] == "vibey-gh"
    listed = surfaces.mcp_dispatch({"id": 2, "method": "tools/list"})
    assert {tool["name"] for tool in listed["result"]["tools"]} == set(surfaces.CAPABILITIES)
    for capability in surfaces.CAPABILITIES:
        response = surfaces.mcp_dispatch(
            {
                "id": 3,
                "method": "tools/call",
                "params": {"name": capability, "arguments": {"arguments": ["--help"]}},
            }
        )
        assert "result" in response
    assert surfaces.mcp_dispatch({"id": 4, "method": "unknown"})["error"]["code"] == -32601
    assert (
        surfaces.mcp_dispatch(
            {"id": 5, "method": "tools/call", "params": {"name": "nope", "arguments": {}}}
        )["error"]["code"]
        == -32602
    )


def test_webhook_authentication_replay_validation_and_full_parity(tmp_path):
    dispatcher = surfaces.WebhookDispatcher(b"secret", _result)
    assert dispatcher.dispatch("1", "bad", b"{}")[0] == 401
    valid_empty = b'{"capability":"version"}'
    empty_signature = "sha256=" + hmac.new(b"secret", valid_empty, hashlib.sha256).hexdigest()
    assert dispatcher.dispatch("", empty_signature, valid_empty)[0] == 409
    for index, capability in enumerate(surfaces.CAPABILITIES):
        body = json.dumps({"capability": capability, "arguments": ["--help"]}).encode()
        signature = "sha256=" + hmac.new(b"secret", body, hashlib.sha256).hexdigest()
        status, payload = dispatcher.dispatch(str(index), signature, body)
        assert status == 200 and payload["capability"] == capability
        assert dispatcher.dispatch(str(index), signature, body)[0] == 409
    bad = b"{}"
    signature = "sha256=" + hmac.new(b"secret", bad, hashlib.sha256).hexdigest()
    assert dispatcher.dispatch("bad", signature, bad)[0] == 400
    with pytest.raises(ValueError, match="secret"):
        surfaces.WebhookDispatcher(b"")

    persistent = surfaces.WebhookDispatcher(b"secret", _result, tmp_path / "deliveries")
    body = b'{"capability":"version"}'
    signature = "sha256=" + hmac.new(b"secret", body, hashlib.sha256).hexdigest()
    assert persistent.dispatch("persistent", signature, body)[0] == 200
    restarted = surfaces.WebhookDispatcher(b"secret", _result, tmp_path / "deliveries")
    assert restarted.dispatch("persistent", signature, body)[0] == 409


def test_cli_projects_api_mcp_sdk_and_webhook(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(surfaces, "invoke", _result)
    for name in ("api", "mcp", "sdk"):
        assert main([name, "version", "--arguments", '["--help"]']) == 0
    monkeypatch.setenv("VIBEY_GH_WEBHOOK_SECRET", "secret")
    monkeypatch.setenv("VIBEY_GH_WEBHOOK_STATE_DIR", str(tmp_path / "deliveries"))
    assert main(["webhook", "version", "--delivery", "delivery"]) == 0
    assert main(["webhook", "version", "--delivery", "delivery"]) == 1
    assert capsys.readouterr().out.count("version") == 4
    assert main(["api", "version", "--arguments", "{}"]) == 1
    assert "JSON array" in capsys.readouterr().err


def test_cli_surface_adapters_propagate_capability_failures(monkeypatch, tmp_path):
    def failed(capability, arguments):
        return surfaces.Result(capability, 7, "", "failed")

    monkeypatch.setattr(surfaces, "invoke", failed)
    monkeypatch.setenv("VIBEY_GH_WEBHOOK_SECRET", "secret")
    monkeypatch.setenv("VIBEY_GH_WEBHOOK_STATE_DIR", str(tmp_path / "deliveries"))
    for name in ("api", "mcp", "sdk"):
        assert main([name, "version"]) == 7
    assert main(["webhook", "version", "--delivery", "failed-delivery"]) == 7
