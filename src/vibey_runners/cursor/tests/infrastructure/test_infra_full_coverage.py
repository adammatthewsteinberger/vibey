# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Drive remaining infrastructure coverage gaps to 100%."""

from __future__ import annotations

import json
import os
import sys
import types
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest
import typer
from typer.testing import CliRunner

from cursorloop.domain.classify import TurnSignals
from cursorloop.domain.model_profile import SHIPPED_PRESETS, ModelProfile
from cursorloop.infrastructure.agent.bridge import (
    LiveBridge,
    launch_bridge_client,
    open_live_bridge,
)
from cursorloop.infrastructure.agent.cli_fallback import (
    CliFallbackGateway,
    build_agent_argv,
    parse_stream_json_lines,
)
from cursorloop.infrastructure.agent.probe import CursorCapacityProbe
from cursorloop.infrastructure.agent.scripted import (
    ALLOW_TEST_AGENT_ENV,
    TEST_AGENT_SCRIPT_ENV,
    ScriptedAgentGateway,
    ScriptedCapacityProbe,
    ScriptedTurn,
    load_agent_script,
    resolve_test_agent_from_env,
)
from cursorloop.infrastructure.api import binder as binder_mod
from cursorloop.infrastructure.api import gateway as gateway_mod
from cursorloop.infrastructure.api import spec as spec_mod
from cursorloop.infrastructure.api.binder import (
    bind_partial_commands,
    json_body_option_help,
    operation_to_click_name,
)
from cursorloop.infrastructure.api.spec import load_spec, operation_ids
from cursorloop.infrastructure.config import load_config
from cursorloop.infrastructure.doctor_env import (
    check_api_key_present,
    check_bridge_binary,
    check_cloud_hooks_clean,
    check_cursor_me,
    check_cursorloop_gitignored,
    check_git_repository,
    check_managed_hooks_state,
    check_mcp_oauth_readiness,
    check_model_in_catalog,
    check_setting_sources,
    findings_as_json,
    resolve_profile,
    run_doctor,
)
from cursorloop.infrastructure.git_savepoints import GitSavePointStore
from cursorloop.infrastructure.run_control import (
    enqueue_cwd,
    enqueue_effort,
    enqueue_model,
    enqueue_prompt,
    enqueue_savepoint,
    enqueue_snapshot,
    enqueue_stop,
)
from cursorloop.infrastructure.rundir import RunDirectory, runs_root_for
from cursorloop.infrastructure.stream_ui.app import StreamUiApp
from tests.fixtures import sdk_payloads

# --- bridge ---


def test_bridge_restore_previous_api_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CURSOR_API_KEY", "prior-key")

    def launch_bridge(**kwargs: object) -> SimpleNamespace:
        del kwargs
        return SimpleNamespace(close=lambda: None)

    bridge = open_live_bridge(
        workspace=tmp_path,
        profile=SHIPPED_PRESETS["composer"],
        api_key="new-key",
        launch_bridge=launch_bridge,
        create_agent=lambda **kwargs: SimpleNamespace(agent_id="a", close=lambda: None),
    )
    assert os.environ["CURSOR_API_KEY"] == "new-key"
    bridge.close()
    assert os.environ["CURSOR_API_KEY"] == "prior-key"


def test_bridge_close_suppresses_agent_and_client_errors(tmp_path: Path) -> None:
    def boom() -> None:
        raise RuntimeError("already closed")

    LiveBridge(
        client=SimpleNamespace(close=boom),
        agent=SimpleNamespace(close=boom),
        owns_client=True,
    ).close()
    LiveBridge(client=object(), agent=object(), owns_client=True).close()
    LiveBridge(
        client=SimpleNamespace(close=lambda: None),
        agent=SimpleNamespace(close=lambda: None),
        owns_client=False,
    ).close()


def test_launch_bridge_client_restores_env_on_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("CURSOR_API_KEY", raising=False)

    def boom(**kwargs: object) -> None:
        del kwargs
        raise RuntimeError("launch failed")

    with pytest.raises(RuntimeError, match="launch failed"):
        launch_bridge_client(tmp_path, api_key="k", launch_bridge=boom)
    assert "CURSOR_API_KEY" not in os.environ


def test_open_live_bridge_reuses_client_and_create_error_cleanup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("CURSOR_API_KEY", raising=False)
    closed: list[str] = []
    existing = SimpleNamespace(close=lambda: closed.append("existing"))

    bridge = open_live_bridge(
        workspace=tmp_path,
        profile=SHIPPED_PRESETS["composer"],
        client=existing,
        create_agent=lambda **kwargs: SimpleNamespace(agent_id="x", close=lambda: None),
    )
    assert bridge.owns_client is False
    bridge.close()
    assert closed == []

    def launch(**kwargs: object) -> SimpleNamespace:
        del kwargs
        return SimpleNamespace(close=lambda: closed.append("owned"))

    def create_fail(**kwargs: object) -> None:
        del kwargs
        raise RuntimeError("create failed")

    with pytest.raises(RuntimeError, match="create failed"):
        open_live_bridge(
            workspace=tmp_path,
            profile=SHIPPED_PRESETS["composer"],
            api_key="temp",
            launch_bridge=launch,
            create_agent=create_fail,
        )
    assert closed == ["owned"]
    assert "CURSOR_API_KEY" not in os.environ

    with pytest.raises(RuntimeError, match="create failed"):
        open_live_bridge(
            workspace=tmp_path,
            profile=SHIPPED_PRESETS["composer"],
            client=object(),
            create_agent=create_fail,
        )

    # owns_client + client without a callable close → skip shutdown, still raise
    with pytest.raises(RuntimeError, match="create failed"):
        open_live_bridge(
            workspace=tmp_path,
            profile=SHIPPED_PRESETS["composer"],
            launch_bridge=lambda **kwargs: object(),
            create_agent=create_fail,
        )


def test_open_live_bridge_create_error_suppresses_client_close_failure(
    tmp_path: Path,
) -> None:
    def launch(**kwargs: object) -> SimpleNamespace:
        del kwargs

        def boom() -> None:
            raise OSError("close fail")

        return SimpleNamespace(close=boom)

    with pytest.raises(RuntimeError, match="create failed"):
        open_live_bridge(
            workspace=tmp_path,
            profile=SHIPPED_PRESETS["composer"],
            launch_bridge=launch,
            create_agent=lambda **kwargs: (_ for _ in ()).throw(RuntimeError("create failed")),
        )


def test_open_live_bridge_resume_error_and_success(tmp_path: Path) -> None:
    def launch(**kwargs: object) -> SimpleNamespace:
        del kwargs
        return SimpleNamespace(close=lambda: None)

    with pytest.raises(RuntimeError, match="resume failed"):
        open_live_bridge(
            workspace=tmp_path,
            profile=SHIPPED_PRESETS["composer"],
            resume_agent_id="bc-9",
            launch_bridge=launch,
            resume_agent=lambda *a, **k: (_ for _ in ()).throw(RuntimeError("resume failed")),
        )

    bridge = open_live_bridge(
        workspace=tmp_path,
        profile=SHIPPED_PRESETS["composer"],
        resume_agent_id="bc-ok",
        launch_bridge=launch,
        resume_agent=lambda agent_id, **kwargs: SimpleNamespace(
            agent_id=agent_id, close=lambda: None
        ),
        create_agent=lambda **kwargs: (_ for _ in ()).throw(AssertionError("create")),
    )
    assert bridge.agent.agent_id == "bc-ok"
    bridge.close()


# --- cli_fallback ---


def test_build_agent_argv_without_force() -> None:
    argv = build_agent_argv(prompt="p", model="composer-2.5", workspace=Path("/ws"), force=False)
    assert "--force" not in argv


def test_parse_stream_json_lines_all_branches() -> None:
    lines = [
        "",
        "not-json-text",
        "42",
        '{"type":"assistant","content":"via-content"}',
        '{"type":"assistant","content":["not-a-string"]}',
        '{"type":"message","delta":"via-delta"}',
        '{"event":"error","error":{"type":"RateLimitError","message":"slow","code":"rl","is_retryable":true,"status":429}}',
        '{"type":"result","error":"plain"}',
        '{"verdict":{"complete":true,"remaining_work":["a"],"blocked_on":"x","summary":"done"}}',
        '{"verdict":{"complete":false,"remaining_work":"skip","summary":""}}',
        '{"agent_id":"cli-1","tokens":9}',
        '{"type":"other"}',
    ]
    outcome = parse_stream_json_lines(lines)
    assert "not-json-text" in outcome.output_text
    assert "via-content" in outcome.output_text
    assert outcome.signals.error_type == "RateLimitError"
    assert outcome.signals.http_status == 429
    assert outcome.verdict is not None
    # Last JSON verdict wins; remaining_work that is not a list → ().
    assert outcome.verdict.complete is False
    assert outcome.verdict.remaining_work == ()
    assert outcome.agent_id == "cli-1"
    assert outcome.tokens == 9

    fenced = (
        "preamble\n```cursorloop-verdict\n"
        '{"complete":false,"remaining_work":["t"],"blocked_on":null,"summary":"s"}\n'
        "```\n"
    )
    from_text = parse_stream_json_lines([json.dumps({"type": "assistant", "text": fenced})])
    assert from_text.verdict is not None
    assert from_text.verdict.complete is False

    assert (
        parse_stream_json_lines(
            [json.dumps({"type": "assistant", "text": "```cursorloop-verdict\nbad"})]
        ).verdict
        is None
    )
    assert (
        parse_stream_json_lines(
            [json.dumps({"type": "assistant", "text": "```cursorloop-verdict\nnot-json\n```"})]
        ).verdict
        is None
    )
    assert (
        parse_stream_json_lines(
            [json.dumps({"type": "assistant", "text": "```cursorloop-verdict\n[]\n```"})]
        ).verdict
        is None
    )
    no_list = parse_stream_json_lines(
        [
            json.dumps(
                {
                    "type": "assistant",
                    "text": (
                        "```cursorloop-verdict\n"
                        '{"complete":true,"remaining_work":"x","summary":"ok"}\n'
                        "```"
                    ),
                }
            )
        ]
    )
    assert no_list.verdict is not None
    assert no_list.verdict.remaining_work == ()


@pytest.mark.asyncio
async def test_cli_fallback_gateway_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def runner(argv: list[str]) -> SimpleNamespace:
        assert argv[0] == "custom-agent"
        return SimpleNamespace(stdout='{"type":"assistant","text":"ok"}\n', returncode=0)

    gw = CliFallbackGateway(workspace=tmp_path, agent_binary="custom-agent", runner=runner)
    await gw.set_profile(SHIPPED_PRESETS["composer"])
    await gw.set_cwd(str(tmp_path))
    assert await gw.cancel_active_run() is False
    outcome = await gw.send_turn("hi", force=True)
    assert "ok" in outcome.output_text
    await gw.close()
    assert gw.closed is True

    bare = CliFallbackGateway(workspace=tmp_path, agent_binary="definitely-missing-agent-xyz")
    monkeypatch.setattr(
        "cursorloop.infrastructure.agent.cli_fallback.shutil.which",
        lambda name: None,
    )
    with pytest.raises(FileNotFoundError, match="not found on PATH"):
        await bare.send_turn("x")

    completed = bare._default_runner([sys.executable, "-c", "print('hi')"])
    assert completed.returncode == 0
    assert "hi" in completed.stdout


# --- probe ---


@pytest.mark.asyncio
async def test_probe_streamed_client_kwarg_and_errors() -> None:
    client = object()
    seen: dict[str, object] = {}

    class NoSend:
        def close(self) -> None:
            seen["closed"] = True

    probe = CursorCapacityProbe(
        "/repo",
        SHIPPED_PRESETS["composer"],
        client=client,
        create_agent=lambda **kwargs: seen.update(kwargs) or NoSend(),
        use_streamed_probe=True,
    )
    with pytest.raises(RuntimeError, match="no send"):
        await probe.probe()
    assert seen.get("client") is client
    assert seen.get("closed") is True

    exc = sdk_payloads.fake_rate_limit_error(code="usage", is_retryable=False, status_code=402)

    class BoomSend:
        def send(self, message: object, *a: object, **k: object) -> object:
            del message, a, k
            raise exc

        def close(self) -> None:
            raise RuntimeError("close noise")

    ok_probe = CursorCapacityProbe(
        "/repo",
        SHIPPED_PRESETS["composer"],
        create_agent=lambda **kwargs: BoomSend(),
        use_streamed_probe=True,
    )
    outcome = await ok_probe.probe()
    assert outcome.signals.error_type == "RateLimitError"

    class RaiseOther:
        def send(self, message: object, *a: object, **k: object) -> object:
            del message, a, k
            raise RuntimeError("bridge down")

        def close(self) -> None:
            return None

    other = CursorCapacityProbe(
        "/repo",
        SHIPPED_PRESETS["composer"],
        create_agent=lambda **kwargs: RaiseOther(),
        use_streamed_probe=True,
    )
    with pytest.raises(RuntimeError, match="bridge down"):
        await other.probe()


# --- scripted ---


@pytest.mark.asyncio
async def test_scripted_gateway_exhausted_and_on_event() -> None:
    events: list[dict[str, object]] = []
    gw = ScriptedAgentGateway(
        [ScriptedTurn(output_text="one", raw_events=({"t": 1},))],
        on_event=events.append,
    )
    await gw.send_turn("a")
    assert events == [{"t": 1}]
    with pytest.raises(IndexError, match="no turns left"):
        await gw.send_turn("b")


@pytest.mark.asyncio
async def test_scripted_probe_exhausted() -> None:
    probe = ScriptedCapacityProbe([TurnSignals()])
    await probe.probe()
    with pytest.raises(IndexError, match="no probes left"):
        await probe.probe()


def test_load_agent_script_validation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    bad_root = tmp_path / "bad.json"
    bad_root.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON object"):
        load_agent_script(bad_root)

    not_lists = tmp_path / "not_lists.json"
    not_lists.write_text('{"probes": {}, "turns": []}', encoding="utf-8")
    with pytest.raises(ValueError, match="must be arrays"):
        load_agent_script(not_lists)

    empty_turns = tmp_path / "empty.json"
    empty_turns.write_text('{"turns": []}', encoding="utf-8")
    with pytest.raises(ValueError, match="at least one turn"):
        load_agent_script(empty_turns)

    bad_turn = tmp_path / "bad_turn.json"
    bad_turn.write_text('{"turns": ["nope"]}', encoding="utf-8")
    with pytest.raises(ValueError, match="each turn must be"):
        load_agent_script(bad_turn)

    bad_events = tmp_path / "bad_events.json"
    bad_events.write_text(
        '{"turns": [{"raw_events": "nope", "output_text": "x"}]}',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="raw_events"):
        load_agent_script(bad_events)

    bad_signals = tmp_path / "bad_signals.json"
    bad_signals.write_text('{"turns": [{"signals": "x"}]}', encoding="utf-8")
    with pytest.raises(ValueError, match="signals must be"):
        load_agent_script(bad_signals)

    bad_verdict = tmp_path / "bad_verdict.json"
    bad_verdict.write_text('{"turns": [{"verdict": "x"}]}', encoding="utf-8")
    with pytest.raises(ValueError, match="verdict must be"):
        load_agent_script(bad_verdict)

    good = tmp_path / "good.json"
    good.write_text(
        json.dumps(
            {
                "probes": [{"signals": {"error_type": "X", "resets_at": "2026-08-13T12:00:00Z"}}],
                "turns": [
                    {
                        "signals": {},
                        "verdict": {
                            "complete": True,
                            "remaining_work": ["a"],
                            "blocked_on": "b",
                            "summary": "s",
                        },
                        "output_text": "done",
                        "cost_usd": None,
                        "raw_events": [{"k": 1}, "skip-me"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    script = load_agent_script(good)
    assert script.turns[0].cost_usd is None
    assert script.turns[0].verdict is not None
    assert script.probes[0].error_type == "X"

    monkeypatch.delenv(ALLOW_TEST_AGENT_ENV, raising=False)
    monkeypatch.delenv(TEST_AGENT_SCRIPT_ENV, raising=False)
    assert resolve_test_agent_from_env() is None

    monkeypatch.setenv(TEST_AGENT_SCRIPT_ENV, str(good))
    with pytest.raises(RuntimeError, match="required"):
        resolve_test_agent_from_env()

    monkeypatch.setenv(ALLOW_TEST_AGENT_ENV, "1")
    resolved = resolve_test_agent_from_env()
    assert resolved is not None


# --- api binder / gateway / spec ---


def test_binder_commands_and_helpers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CURSOR_API_KEY", "k")
    app = typer.Typer()
    bound = bind_partial_commands(app)
    assert {b.operation_id for b in bound} == binder_mod.PARTIAL_OPERATIONS
    assert operation_to_click_name("getMe") == "get-me"
    assert "--json" in json_body_option_help()

    runner = CliRunner()
    body_file = tmp_path / "body.json"
    body_file.write_text('{"name":"x"}', encoding="utf-8")

    with patch.object(binder_mod, "CloudAgentsGateway") as gw_cls:
        inst = gw_cls.return_value.__enter__.return_value
        inst.invoke.return_value = {"ok": True}
        assert runner.invoke(app, ["me"]).exit_code == 0
        assert runner.invoke(app, ["models"]).exit_code == 0
        assert runner.invoke(app, ["create", "--json", '{"a":1}']).exit_code == 0
        assert runner.invoke(app, ["create", "--json-file", str(body_file)]).exit_code == 0
        assert runner.invoke(app, ["create"]).exit_code == 2
        assert runner.invoke(app, ["get", "agent-1"]).exit_code == 0
        assert runner.invoke(app, ["cancel", "agent-1"]).exit_code == 0

    with patch.object(binder_mod, "CloudAgentsGateway") as gw_cls:
        gw_cls.return_value.__enter__.side_effect = httpx.ConnectError("down")
        for args in (["me"], ["models"], ["create", "--json", "{}"], ["get", "a"], ["cancel", "a"]):
            assert runner.invoke(app, args).exit_code == 1

    monkeypatch.delenv("CURSOR_API_KEY", raising=False)
    assert runner.invoke(app, ["me"]).exit_code == 1

    monkeypatch.setattr(
        binder_mod,
        "PARTIAL_OPERATIONS",
        frozenset({"getMe", "listModels", "createAgent", "getAgent", "cancelAgent", "extraOp"}),
    )
    with pytest.raises(RuntimeError, match="missing operations"):
        bind_partial_commands(typer.Typer())


def test_api_gateway_edge_paths() -> None:
    empty = httpx.MockTransport(lambda request: httpx.Response(200, content=b""))
    owned = gateway_mod.CloudAgentsGateway(
        api_key="k",
        client=httpx.Client(base_url="https://api.cursor.com", transport=empty),
    )
    # Injected client → owns_client False; close is a no-op on ownership.
    owned._owns_client = True
    assert owned.invoke("GET", "/v1/me") == {}
    owned.close()

    def list_payload(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=["a", "b"])

    client = httpx.Client(
        base_url="https://api.cursor.com", transport=httpx.MockTransport(list_payload)
    )
    with gateway_mod.CloudAgentsGateway(api_key="k", client=client) as gw:
        assert gw.invoke("GET", "/v1/models") == {"data": ["a", "b"]}

    def dict_redacts_to_str(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"x": 1})

    client2 = httpx.Client(
        base_url="https://api.cursor.com",
        transport=httpx.MockTransport(dict_redacts_to_str),
    )
    with (
        patch("cursorloop.infrastructure.api.gateway.redact", return_value="scrubbed"),
        gateway_mod.CloudAgentsGateway(api_key="k", client=client2) as gw,
    ):
        assert gw.invoke("GET", "/v1/me") == {"data": "scrubbed"}

    # Default-constructed client owns the connection (line 29).
    with patch("cursorloop.infrastructure.api.gateway.httpx.Client") as client_cls:
        fake = MagicMock()
        client_cls.return_value = fake
        gw = gateway_mod.CloudAgentsGateway(api_key="k")
        gw.close()
        fake.close.assert_called_once()


def test_spec_operation_id_edge_cases(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    weird = {
        "openapi": "3.0.3",
        "info": {"title": "t", "version": "0"},
        "paths": {
            "/ok": {
                "get": {"operationId": "good"},
                "x-foo": {"operationId": "ignored"},
                "post": "not-a-dict",
                "put": {"operationId": ""},
                "patch": {},
            },
            "/skip": "not-a-mapping",
        },
    }
    assert "good" in operation_ids(weird)
    assert operation_ids({"paths": []}) == frozenset()

    path = tmp_path / "spec.yaml"
    path.write_text("- just a list\n", encoding="utf-8")
    digest = spec_mod.digest_of(path.read_bytes())
    monkeypatch.setattr(spec_mod, "VENDORED_SPEC_DIGEST", digest)
    monkeypatch.setattr(spec_mod, "SPEC_PATH", path)
    with pytest.raises(ValueError, match="mapping"):
        load_spec(path)


# --- config ---


def test_config_timeout_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CURSORLOOP_TURN_TIMEOUT", "12.5")
    monkeypatch.setenv("CURSORLOOP_STALL_TIMEOUT", "3")
    cfg = load_config()
    assert cfg.turn_timeout_seconds == 12.5
    assert cfg.stall_timeout_seconds == 3.0


# --- doctor_env ---


def test_doctor_env_remaining_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    assert check_api_key_present(None).level == "fail"
    assert check_cursor_me(api_key=None).level == "fail"

    (tmp_path / ".cursor").mkdir()
    (tmp_path / ".cursor" / "mcp.json").write_text("{bad", encoding="utf-8")
    assert check_mcp_oauth_readiness(workspace=tmp_path, saved_logins=frozenset()) == []

    (tmp_path / ".cursor" / "mcp.json").write_text(
        '{"mcpServers": []}',
        encoding="utf-8",
    )
    assert check_mcp_oauth_readiness(workspace=tmp_path, saved_logins=frozenset()) == []

    (tmp_path / ".cursor" / "mcp.json").write_text(
        '{"mcpServers": {"x": "not-dict", "y": {"url": "https://x", "command": "c"}}}',
        encoding="utf-8",
    )
    # url+command → treated as local command (pass finding), not OAuth-fail
    findings = check_mcp_oauth_readiness(workspace=tmp_path, saved_logins=frozenset())
    assert all(f.level != "fail" for f in findings)

    (tmp_path / ".cursor" / "mcp.json").write_text(
        json.dumps(
            {
                "mcpServers": {
                    "remote": {"url": "https://mcp.example"},
                    "local": {"command": "npx"},
                }
            }
        ),
        encoding="utf-8",
    )
    oauth = check_mcp_oauth_readiness(workspace=tmp_path, saved_logins=frozenset())
    assert any(f.name == "mcp-oauth:remote" and f.level == "fail" for f in oauth)
    assert any(f.name == "mcp-local:local" and f.level == "pass" for f in oauth)
    svc = check_mcp_oauth_readiness(
        workspace=tmp_path, saved_logins=frozenset({"remote"}), is_service_account=True
    )
    assert any(f.name == "mcp-oauth:remote" and f.level == "fail" for f in svc)

    assert check_mcp_oauth_readiness(workspace=tmp_path / "missing", saved_logins=frozenset()) == []

    def boom_me(**kwargs: object) -> None:
        raise RuntimeError("auth")

    with patch("cursorloop.infrastructure.doctor_env.Cursor.me", side_effect=boom_me):
        assert check_cursor_me(api_key="k").level == "fail"
    with patch(
        "cursorloop.infrastructure.doctor_env.Cursor.me",
        return_value=SimpleNamespace(email="u@example.com"),
    ):
        assert check_cursor_me(api_key="k").level == "pass"

    with patch(
        "cursorloop.infrastructure.doctor_env.subprocess.run",
        side_effect=OSError("exec"),
    ):
        assert check_bridge_binary(which=lambda name: "/bin/bridge").level == "fail"

    with patch(
        "cursorloop.infrastructure.doctor_env.subprocess.run",
        return_value=SimpleNamespace(returncode=1, stdout="", stderr=""),
    ):
        assert check_bridge_binary(which=lambda name: "/bin/bridge").level == "fail"
    with patch(
        "cursorloop.infrastructure.doctor_env.subprocess.run",
        return_value=SimpleNamespace(returncode=0, stdout="help", stderr=""),
    ):
        assert check_bridge_binary(which=lambda name: "/bin/bridge").level == "pass"

    assert (
        check_model_in_catalog(profile=SHIPPED_PRESETS["composer"], api_key=None)[0].level == "fail"
    )

    with patch("cursorloop.infrastructure.doctor_env.Cursor.models.list", side_effect=RuntimeError):
        assert (
            check_model_in_catalog(profile=SHIPPED_PRESETS["composer"], api_key="k")[0].level
            == "fail"
        )

    missing_model = check_model_in_catalog(
        profile=SHIPPED_PRESETS["composer"],
        api_key="k",
        models_fn=lambda **kwargs: [SimpleNamespace(id="other")],
    )
    assert missing_model[0].level == "fail"

    no_auto = check_model_in_catalog(
        profile=SHIPPED_PRESETS["router-cost"],
        api_key="k",
        models_fn=lambda **kwargs: [SimpleNamespace(id="composer-2.5")],
    )
    assert any(f.name == "models-catalog" and f.level == "fail" for f in no_auto)

    router_absent = check_model_in_catalog(
        profile=ModelProfile(model_id="auto-smart", params=(("optimize_for", "cost"),)),
        api_key="k",
        models_fn=lambda **kwargs: [SimpleNamespace(id="composer-2.5")],
    )
    assert any(f.name == "router-availability" and f.level == "fail" for f in router_absent)

    no_opt = check_model_in_catalog(
        profile=ModelProfile(model_id="auto-smart"),
        api_key="k",
        models_fn=lambda **kwargs: [SimpleNamespace(id="auto-smart")],
    )
    assert any(f.name == "router-availability" and f.level == "warn" for f in no_opt)

    bad_opt = check_model_in_catalog(
        profile=ModelProfile(model_id="auto-smart", params=(("optimize_for", "nope"),)),
        api_key="k",
        models_fn=lambda **kwargs: [SimpleNamespace(id="auto-smart")],
    )
    assert any(f.name == "router-availability" and f.level == "fail" for f in bad_opt)

    good_router = check_model_in_catalog(
        profile=SHIPPED_PRESETS["router-intelligence"],
        api_key="k",
        models_fn=lambda **kwargs: [SimpleNamespace(id="auto-smart")],
    )
    assert any(f.name == "router-availability" and f.level == "pass" for f in good_router)

    hermetic = check_setting_sources(sources=())
    assert hermetic.level == "pass"
    user_sources = check_setting_sources(sources=("user",))
    assert user_sources.level == "warn"
    assert "user" in user_sources.detail

    assert check_git_repository(Path("/")).level == "fail"
    git_ws = tmp_path / "gitws"
    git_ws.mkdir()
    (git_ws / ".git").mkdir()
    assert check_git_repository(git_ws).level == "pass"
    nested = git_ws / "sub"
    nested.mkdir()
    assert check_git_repository(nested).level == "pass"
    orphan = tmp_path / "orphan-no-git"
    orphan.mkdir()
    assert check_git_repository(orphan).level == "warn"

    # Installed managed hooks → warn
    from cursorloop.infrastructure.agent.hooks import ManagedHooks

    hooks_ws = tmp_path / "hooks-ws"
    hooks_ws.mkdir()
    ManagedHooks(workspace=hooks_ws, state_dir=hooks_ws / ".cursorloop").install()
    assert check_managed_hooks_state(hooks_ws).level == "warn"

    assert check_cloud_hooks_clean(cloud=False, workspace=tmp_path).level == "pass"
    assert check_cloud_hooks_clean(cloud=True, workspace=tmp_path).level == "pass"
    hooks_file = tmp_path / ".cursor" / "hooks.json"
    hooks_file.parent.mkdir(parents=True, exist_ok=True)
    hooks_file.write_text("{}", encoding="utf-8")
    with patch(
        "cursorloop.infrastructure.doctor_env.subprocess.run",
        return_value=SimpleNamespace(returncode=1, stdout="", stderr=""),
    ):
        assert check_cloud_hooks_clean(cloud=True, workspace=tmp_path).level == "warn"
    with patch(
        "cursorloop.infrastructure.doctor_env.subprocess.run",
        return_value=SimpleNamespace(returncode=0, stdout=" M .cursor/hooks.json\n", stderr=""),
    ):
        assert check_cloud_hooks_clean(cloud=True, workspace=tmp_path).level == "fail"
    with patch(
        "cursorloop.infrastructure.doctor_env.subprocess.run",
        return_value=SimpleNamespace(returncode=0, stdout="", stderr=""),
    ):
        assert check_cloud_hooks_clean(cloud=True, workspace=tmp_path).level == "pass"

    bare = tmp_path / "bare"
    bare.mkdir()
    assert check_cursorloop_gitignored(bare).level == "warn"
    (bare / ".gitignore").write_text("node_modules/\n", encoding="utf-8")
    assert check_cursorloop_gitignored(bare).level == "fail"
    (bare / ".gitignore").write_text(".cursorloop/\n", encoding="utf-8")
    assert check_cursorloop_gitignored(bare).level == "pass"

    assert resolve_profile("composer") == SHIPPED_PRESETS["composer"]
    assert resolve_profile("custom-model").model_id == "custom-model"
    assert resolve_profile(None) == SHIPPED_PRESETS["composer"]

    live = run_doctor(
        workspace=tmp_path,
        api_key="k",
        live=True,
        me_fn=lambda **kwargs: SimpleNamespace(email="e@x"),
        models_fn=lambda **kwargs: [SimpleNamespace(id="composer-2.5")],
        which=lambda name: None,
        model="composer",
        setting_sources=("project", "user"),
        cloud=True,
    )
    assert any(f.name == "cursor-me" for f in live)
    assert "fail" in findings_as_json(live) or "pass" in findings_as_json(live)

    # _needs_oauth non-dict
    from cursorloop.infrastructure import doctor_env as de

    assert de._needs_oauth("x") is False
    assert "OAuth" in de._safe_detail("n", {"url": "https://x"})


# --- git_savepoints ---


def test_git_savepoints_mocked(tmp_path: Path) -> None:
    index = tmp_path / "savepoints.jsonl"
    index.write_text("", encoding="utf-8")  # already exists → skip touch
    store = GitSavePointStore(cwd=tmp_path, index_path=index)
    # Re-init on existing index covers the exists() true branch.
    GitSavePointStore(cwd=tmp_path, index_path=index)

    def run(argv: list[str], *, check: bool = True) -> SimpleNamespace:
        cmd = argv[1] if len(argv) > 1 else ""
        if argv[:3] == ["git", "rev-parse", "--is-inside-work-tree"]:
            return SimpleNamespace(returncode=0, stdout="true\n", stderr="")
        if argv[:2] == ["git", "add"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if argv[:2] == ["git", "reset"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if argv[:3] == ["git", "diff", "--cached"]:
            return SimpleNamespace(returncode=1, stdout="", stderr="")  # has staged
        if argv[:2] == ["git", "commit"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if argv[:2] == ["git", "rev-parse"] and argv[-1] == "HEAD":
            return SimpleNamespace(returncode=0, stdout="abc123\n", stderr="")
        if argv[:2] == ["git", "update-ref"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if argv[:2] == ["git", "status"]:
            return SimpleNamespace(returncode=0, stdout=" M file\n", stderr="")
        if argv[:2] == ["git", "diff"]:
            return SimpleNamespace(returncode=0, stdout="1 file changed\n", stderr="")
        if argv[:2] == ["git", "reset"] or "reset" in argv:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        del check, cmd
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    with patch.object(store, "_run", side_effect=run):
        point = store.create(run_id="r1", label="after-turn", message="msg")
        assert point is not None
        assert point.sha == "abc123"
        # Blank lines + other-run refs are skipped by list_points.
        with index.open("a", encoding="utf-8") as fh:
            fh.write("\n")
            fh.write(
                json.dumps(
                    {
                        "n": 9,
                        "ref": "refs/cursorloop/other/after-turn",
                        "sha": "zzz",
                        "label": "x",
                        "created_at": "t",
                    }
                )
                + "\n"
            )
        assert len(store.list_points("r1")) == 1
        assert store.unwind(run_id="r1", to="abc123", backup=True) == {"sha": "abc123"}
        assert "M file" in store.changes_since(None)
        assert "file changed" in store.changes_since("abc123")

    index.write_text(
        "\n"
        + json.dumps(
            {
                "n": 1,
                "ref": "refs/cursorloop/other/1",
                "sha": "x",
                "label": "x",
                "created_at": "t",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    assert store.list_points("r1") == []

    empty_index = tmp_path / "missing.jsonl"
    store2 = GitSavePointStore(cwd=tmp_path, index_path=empty_index)
    empty_index.unlink()
    assert store2.list_points("r1") == []

    with patch.object(
        store2,
        "_run",
        return_value=SimpleNamespace(returncode=1, stdout="", stderr=""),
    ):
        assert store2.create(run_id="r1", label="x") is None

    # Exercise real _run with a harmless git invocation (cwd may not be a repo).
    result = store2._run(["git", "rev-parse", "--is-inside-work-tree"], check=False)
    assert result.returncode in {0, 128}


def test_git_savepoints_no_staged_still_tags(tmp_path: Path) -> None:
    store = GitSavePointStore(cwd=tmp_path, index_path=tmp_path / "idx.jsonl")
    calls: list[list[str]] = []

    def run(argv: list[str], *, check: bool = True) -> SimpleNamespace:
        calls.append(argv)
        if argv[:3] == ["git", "rev-parse", "--is-inside-work-tree"]:
            return SimpleNamespace(returncode=0, stdout="true\n", stderr="")
        if argv[:3] == ["git", "diff", "--cached"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")  # clean
        if argv[:2] == ["git", "rev-parse"] and argv[-1] == "HEAD":
            return SimpleNamespace(returncode=0, stdout="deadbeef\n", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    with patch.object(store, "_run", side_effect=run):
        point = store.create(run_id="r2", label="noop")
    assert point is not None
    assert not any(c[:2] == ["git", "commit"] for c in calls)


# --- run_control ---


def test_run_control_enqueue_helpers(tmp_path: Path) -> None:
    cwd = tmp_path / "ws"
    cwd.mkdir()
    root = runs_root_for(cwd)
    RunDirectory.create(root, cwd=cwd)
    assert enqueue_stop(cwd).run_id
    assert enqueue_prompt(cwd, "more").run_id
    assert enqueue_model(cwd, "composer-2.5").run_id
    assert enqueue_effort(cwd, "high").run_id
    assert enqueue_cwd(cwd, str(cwd)).run_id
    assert enqueue_snapshot(cwd).run_id
    assert enqueue_savepoint(cwd).run_id


# --- stream_ui ---


def test_stream_ui_run_without_textual(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = __import__

    def fake_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "textual" or name.startswith("textual."):
            raise ImportError("no textual")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)
    ui = StreamUiApp()
    ui.run()
    assert ui._running is False


def test_stream_ui_run_with_fake_textual(monkeypatch: pytest.MonkeyPatch) -> None:
    writes: list[str] = []

    class FakeRichLog:
        def __init__(self, id: str | None = None) -> None:
            self.id = id

        def write(self, text: str) -> None:
            writes.append(text)

    class FakeApp:
        CSS = ""

        def __class_getitem__(cls, item: object) -> type:
            return cls

        def query_one(self, selector: str, typ: type) -> FakeRichLog:
            del selector, typ
            return FakeRichLog(id="stream")

        def run(self) -> None:
            list(self.compose())
            self.on_mount()

    fake_app_mod = types.ModuleType("textual.app")
    fake_app_mod.App = FakeApp  # type: ignore[attr-defined]
    fake_app_mod.ComposeResult = object  # type: ignore[attr-defined]
    fake_widgets = types.ModuleType("textual.widgets")
    fake_widgets.RichLog = FakeRichLog  # type: ignore[attr-defined]
    fake_textual = types.ModuleType("textual")
    monkeypatch.setitem(sys.modules, "textual", fake_textual)
    monkeypatch.setitem(sys.modules, "textual.app", fake_app_mod)
    monkeypatch.setitem(sys.modules, "textual.widgets", fake_widgets)

    ui = StreamUiApp()
    ui.on_delta("hello")
    ui.on_step({"phase": "RUNNING"})
    ui.run()
    assert ui._running is False
    assert any("hello" in w for w in writes)
    assert any("RUNNING" in w for w in writes)
