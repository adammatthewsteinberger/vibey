# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Unit tests for the scripted test-agent gate."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from codexloop.domain.completion import DEFAULT_DONE_MARKER
from codexloop.domain.model_profile import Effort, ModelEffortProfile
from codexloop.domain.signals import TurnSignals
from codexloop.infrastructure.agent.scripted import (
    ALLOW_TEST_AGENT_ENV,
    TEST_AGENT_SCRIPT_ENV,
    ScriptedAgentGateway,
    ScriptedCapacityProbe,
    ScriptedTurn,
    load_agent_script,
    resolve_test_agent_from_env,
)


def test_script_without_allow_raises(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    script = tmp_path / "s.json"
    script.write_text('{"probes":[{}],"turns":[{"signals":{}}]}', encoding="utf-8")
    monkeypatch.setenv(TEST_AGENT_SCRIPT_ENV, str(script))
    monkeypatch.delenv(ALLOW_TEST_AGENT_ENV, raising=False)
    with pytest.raises(RuntimeError, match=ALLOW_TEST_AGENT_ENV):
        resolve_test_agent_from_env()


def test_resolve_loads_when_both_set(monkeypatch: pytest.MonkeyPatch) -> None:
    fixtures = Path(__file__).resolve().parents[1] / "live" / "fixtures" / "agent_scripts"
    monkeypatch.setenv(ALLOW_TEST_AGENT_ENV, "1")
    monkeypatch.setenv(TEST_AGENT_SCRIPT_ENV, str(fixtures / "done.json"))
    pair = resolve_test_agent_from_env()
    assert pair is not None
    gateway, probe = pair
    assert gateway is not None
    assert probe is not None


def test_resolve_none_without_script(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(TEST_AGENT_SCRIPT_ENV, raising=False)
    monkeypatch.setenv(ALLOW_TEST_AGENT_ENV, "1")
    assert resolve_test_agent_from_env() is None


def test_resolve_none_with_disallowed_allow_value(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    script = tmp_path / "s.json"
    script.write_text('{"turns":[{"signals":{}}]}', encoding="utf-8")
    monkeypatch.setenv(TEST_AGENT_SCRIPT_ENV, str(script))
    monkeypatch.setenv(ALLOW_TEST_AGENT_ENV, "maybe")
    with pytest.raises(RuntimeError):
        resolve_test_agent_from_env()


def test_load_done_script() -> None:
    fixtures = Path(__file__).resolve().parents[1] / "live" / "fixtures" / "agent_scripts"
    script = load_agent_script(fixtures / "done.json")
    assert len(script.turns) == 1
    assert script.turns[0].signals.final_message == DEFAULT_DONE_MARKER


def test_load_agent_script_validation(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON object"):
        load_agent_script(bad)

    bad.write_text('{"probes":{},"turns":[]}', encoding="utf-8")
    with pytest.raises(ValueError, match="arrays"):
        load_agent_script(bad)

    bad.write_text('{"turns":[]}', encoding="utf-8")
    with pytest.raises(ValueError, match="at least one turn"):
        load_agent_script(bad)

    bad.write_text('{"turns":["x"]}', encoding="utf-8")
    with pytest.raises(ValueError, match="JSON object"):
        load_agent_script(bad)

    bad.write_text('{"turns":[{"signals":[]}]}', encoding="utf-8")
    with pytest.raises(ValueError, match="signals"):
        load_agent_script(bad)


def test_load_parses_windows_and_nested_signals(tmp_path: Path) -> None:
    path = tmp_path / "s.json"
    path.write_text(
        json.dumps(
            {
                "probes": [
                    {
                        "signals": {
                            "plan_windows": {
                                "primary": {"window_minutes": 5, "used_percent": 10},
                                "secondary": "bad",
                                "plan_type": "plus",
                                "rate_limit_reached_type": "primary",
                            }
                        }
                    },
                    {"plan_windows": None},
                ],
                "turns": [
                    {
                        "signals": {"completed": True},
                        "thread_id": None,
                        "cost_dollars": 1.5,
                    },
                    {
                        "signals": {
                            "plan_windows": {
                                "primary": None,
                                "secondary": {"window_minutes": "x"},
                            }
                        }
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    script = load_agent_script(path)
    assert script.probes[0].plan_windows is not None
    assert script.probes[0].plan_windows.plan_type == "plus"
    assert script.probes[1].plan_windows is None
    assert script.turns[0].thread_id is None
    assert script.turns[0].cost_dollars == 1.5

    path.write_text(
        json.dumps({"turns": [{"signals": {"plan_windows": []}}]}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="plan_windows"):
        load_agent_script(path)


@pytest.mark.anyio
async def test_scripted_gateway_and_probe_behavior() -> None:
    from codexloop.application.ports import PermissionMode

    gateway = ScriptedAgentGateway([ScriptedTurn(signals=TurnSignals(completed=True))])
    outcome = await gateway.send_turn("hi")
    assert outcome.signals.completed is True
    with pytest.raises(IndexError):
        await gateway.send_turn("again")
    await gateway.close()
    assert gateway.closed
    await gateway.set_profile(ModelEffortProfile(model="gpt-5", effort=Effort.HIGH))
    await gateway.set_permission_mode(PermissionMode.AUTONOMOUS)
    await gateway.set_cwd("/tmp")
    await gateway.set_session_resources({"a": 1})
    assert gateway.resolve_tool_approval("r1", allow=True, reason="ok") is True

    probe = ScriptedCapacityProbe([TurnSignals()])
    result = await probe.probe()
    assert result.outcome is not None
    with pytest.raises(IndexError):
        await probe.probe()
