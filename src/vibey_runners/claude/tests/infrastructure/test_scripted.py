# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Coverage-focused tests for infrastructure/agent/scripted.py.

Complements test_scripted_agent.py by exercising the setter methods,
the empty-script IndexError paths, and every ValueError branch in the
JSON-script parsing helpers.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from claudeloop.domain.classify import TurnSignals
from claudeloop.domain.model_profile import ModelEffortProfile
from claudeloop.infrastructure.agent.scripted import (
    ALLOW_TEST_AGENT_ENV,
    TEST_AGENT_SCRIPT_ENV,
    ScriptedAgentGateway,
    ScriptedCapacityProbe,
    ScriptedTurn,
    _parse_signals,
    _parse_turn,
    _parse_verdict,
    load_agent_script,
    resolve_test_agent_from_env,
)


@pytest.mark.asyncio
async def test_set_profile_logs_and_records() -> None:
    gateway = ScriptedAgentGateway([ScriptedTurn()])
    profile = ModelEffortProfile(model="claude-opus-4-6", effort="high", preset="medium")
    await gateway.set_profile(profile)
    assert gateway.profiles == [profile]


@pytest.mark.asyncio
async def test_set_permission_mode_records() -> None:
    gateway = ScriptedAgentGateway([ScriptedTurn()])
    await gateway.set_permission_mode("acceptEdits")
    assert gateway.permission_modes == ["acceptEdits"]


@pytest.mark.asyncio
async def test_set_cwd_records() -> None:
    gateway = ScriptedAgentGateway([ScriptedTurn()])
    await gateway.set_cwd("/tmp/somewhere")
    assert gateway.cwds == ["/tmp/somewhere"]


@pytest.mark.asyncio
async def test_set_session_resources_records_kwargs() -> None:
    gateway = ScriptedAgentGateway([ScriptedTurn()])
    await gateway.set_session_resources(max_turns=5, budget_usd=1.5)
    assert gateway.resource_updates == [{"max_turns": 5, "budget_usd": 1.5}]


def test_resolve_tool_approval_records_and_returns_true() -> None:
    gateway = ScriptedAgentGateway([ScriptedTurn()])
    result = gateway.resolve_tool_approval("req-1", allow=False, reason="denied by policy")
    assert result is True
    assert gateway.tool_resolutions == [("req-1", False, "denied by policy")]


def test_resolve_tool_approval_default_reason() -> None:
    gateway = ScriptedAgentGateway([ScriptedTurn()])
    gateway.resolve_tool_approval("req-2", allow=True)
    assert gateway.tool_resolutions == [("req-2", True, "")]


@pytest.mark.asyncio
async def test_send_turn_raises_index_error_when_script_empty() -> None:
    gateway = ScriptedAgentGateway([])
    with pytest.raises(IndexError, match="no turns left in script"):
        await gateway.send_turn("hello")


@pytest.mark.asyncio
async def test_send_turn_without_on_event_skips_event_dispatch() -> None:
    turn = ScriptedTurn(raw_events=({"foo": "bar"},))
    gateway = ScriptedAgentGateway([turn])
    outcome = await gateway.send_turn("hello")
    assert outcome.raw_events == ({"foo": "bar"},)


@pytest.mark.asyncio
async def test_capacity_probe_raises_index_error_when_script_empty() -> None:
    probe = ScriptedCapacityProbe([])
    with pytest.raises(IndexError, match="no probes left in script"):
        await probe.probe()


@pytest.mark.asyncio
async def test_capacity_probe_returns_signals() -> None:
    signals = TurnSignals(rate_limit_status="allowed")
    probe = ScriptedCapacityProbe([signals])
    outcome = await probe.probe()
    assert outcome.signals is signals
    assert outcome.verdict is None
    assert outcome.session_id is None


def test_load_agent_script_root_not_dict(tmp_path: Path) -> None:
    path = tmp_path / "script.json"
    path.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    with pytest.raises(ValueError, match="root must be a JSON object"):
        load_agent_script(path)


def test_load_agent_script_probes_not_array(tmp_path: Path) -> None:
    path = tmp_path / "script.json"
    path.write_text(
        json.dumps({"probes": "not-a-list", "turns": [{}]}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="must be arrays"):
        load_agent_script(path)


def test_load_agent_script_turns_not_array(tmp_path: Path) -> None:
    path = tmp_path / "script.json"
    path.write_text(
        json.dumps({"probes": [{}], "turns": "not-a-list"}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="must be arrays"):
        load_agent_script(path)


def test_load_agent_script_empty_turns_raises(tmp_path: Path) -> None:
    path = tmp_path / "script.json"
    path.write_text(json.dumps({"probes": [{}], "turns": []}), encoding="utf-8")
    with pytest.raises(ValueError, match="at least one turn"):
        load_agent_script(path)


def test_resolve_test_agent_returns_none_when_script_path_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(ALLOW_TEST_AGENT_ENV, "1")
    monkeypatch.setenv(TEST_AGENT_SCRIPT_ENV, "")
    assert resolve_test_agent_from_env() is None


def test_parse_turn_item_not_dict_raises() -> None:
    with pytest.raises(ValueError, match="each turn must be a JSON object"):
        _parse_turn(["not", "a", "dict"])


def test_parse_turn_raw_events_not_list_raises() -> None:
    with pytest.raises(ValueError, match="raw_events must be an array"):
        _parse_turn({"raw_events": "not-a-list"})


def test_parse_turn_filters_non_dict_raw_events() -> None:
    turn = _parse_turn({"raw_events": [{"a": 1}, "skip-me", 42]})
    assert turn.raw_events == ({"a": 1},)


def test_parse_signals_item_not_dict_raises() -> None:
    with pytest.raises(ValueError, match="signals must be a JSON object"):
        _parse_signals(["not", "a", "dict"])


def test_parse_signals_unwraps_signals_key() -> None:
    signals = _parse_signals({"signals": {"rate_limit_status": "allowed"}})
    assert signals.rate_limit_status == "allowed"


def test_parse_verdict_item_not_dict_raises() -> None:
    with pytest.raises(ValueError, match="verdict must be a JSON object"):
        _parse_verdict(["not", "a", "dict"])


def test_parse_verdict_parses_full_fields() -> None:
    verdict = _parse_verdict(
        {
            "complete": True,
            "remaining_work": ["a", "b"],
            "blocked_on": "waiting on human",
            "summary": "done-ish",
        }
    )
    assert verdict.complete is True
    assert verdict.remaining_work == ("a", "b")
    assert verdict.blocked_on == "waiting on human"
    assert verdict.summary == "done-ish"
