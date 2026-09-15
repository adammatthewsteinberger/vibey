# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""SDK gateway wraps Agent(config) as an async CM and maps drain errors."""

from __future__ import annotations

import json
import logging
from unittest.mock import patch

import pytest
from google.antigravity.types import AntigravityExecutionError, AntigravityValidationError

from agyloop.application.dto import TurnOutcome
from agyloop.domain.classify import TurnSignals
from agyloop.domain.completion import Blocked, Continue, Done, evaluate
from agyloop.domain.errors import AgentConfigError
from agyloop.infrastructure.agent.gateway import AntigravityAgentGateway


class _FakeResponse:
    def __init__(
        self,
        *,
        text: str = "",
        error: BaseException | None = None,
        structured: dict[str, object] | None = None,
        log_line: str | None = None,
    ) -> None:
        self._text = text
        self._error = error
        self._structured = structured
        self._log_line = log_line

    async def text(self) -> str:
        if self._log_line is not None:
            logging.getLogger("google.antigravity").error(self._log_line)
        if self._error is not None:
            raise self._error
        return self._text

    async def structured_output(self) -> dict[str, object] | None:
        if self._error is not None:
            raise self._error
        return self._structured

    async def resolve(self) -> list[object]:
        if self._error is not None:
            raise self._error
        return []


class _FakeAgent:
    def __init__(self, config: object) -> None:
        self.config = config
        self.conversation_id = "c" * 32
        self.prompts: list[str] = []
        self.closed = False
        self.response: _FakeResponse = _FakeResponse(text="ok")

    async def __aenter__(self) -> _FakeAgent:
        return self

    async def __aexit__(self, *args: object) -> None:
        self.closed = True

    async def chat(self, prompt: str) -> _FakeResponse:
        self.prompts.append(prompt)
        return self.response


@pytest.fixture
def fake_agent() -> _FakeAgent:
    agent = _FakeAgent(config=None)

    def _factory(config: object) -> _FakeAgent:
        agent.config = config
        return agent

    with patch("agyloop.infrastructure.agent.gateway.Agent", side_effect=_factory):
        yield agent


async def test_send_turn_drains_chat_and_returns_turn_outcome(fake_agent: _FakeAgent) -> None:
    fake_agent.response = _FakeResponse(text="hello from gemini")
    gateway = AntigravityAgentGateway(cwd=".")
    outcome = await gateway.send_turn("do the work")
    await gateway.close()
    assert isinstance(outcome, TurnOutcome)
    assert isinstance(outcome.signals, TurnSignals)
    assert outcome.output_text == "hello from gemini"
    assert outcome.session_id == "c" * 32
    assert fake_agent.prompts == ["do the work"]
    assert fake_agent.closed is True


async def test_send_turn_maps_execution_error_to_signals(fake_agent: _FakeAgent) -> None:
    fake_agent.response = _FakeResponse(
        error=AntigravityExecutionError("429 RESOURCE_EXHAUSTED: quota")
    )
    gateway = AntigravityAgentGateway(cwd=".")
    outcome = await gateway.send_turn("go")
    await gateway.close()
    assert outcome.signals.exception_type == "AntigravityExecutionError"
    assert outcome.signals.http_status == 429
    assert outcome.session_id == "c" * 32


async def test_send_turn_validation_error_is_our_bug(fake_agent: _FakeAgent) -> None:
    fake_agent.response = _FakeResponse(error=AntigravityValidationError("invalid config field"))
    gateway = AntigravityAgentGateway(cwd=".")
    with pytest.raises(AgentConfigError):
        await gateway.send_turn("go")
    await gateway.close()


async def test_send_turn_404_is_config_error(fake_agent: _FakeAgent) -> None:
    fake_agent.response = _FakeResponse(
        error=AntigravityExecutionError("404 NOT_FOUND: model is no longer available to new users")
    )
    gateway = AntigravityAgentGateway(cwd=".")
    with pytest.raises(AgentConfigError, match="404|NOT_FOUND|withdrawn"):
        await gateway.send_turn("go")
    await gateway.close()


async def test_send_turn_does_not_return_vendor_types(fake_agent: _FakeAgent) -> None:
    gateway = AntigravityAgentGateway(cwd=".")
    outcome = await gateway.send_turn("go")
    await gateway.close()
    assert "antigravity" not in type(outcome).__module__
    assert "antigravity" not in type(outcome.signals).__module__


async def test_set_permission_mode_accepts_agyloop_enum_not_vendor_types(
    fake_agent: _FakeAgent,
) -> None:
    gateway = AntigravityAgentGateway(cwd=".")
    await gateway.set_permission_mode("scoped")
    await gateway.send_turn("go")
    await gateway.close()
    assert fake_agent.config is not None


async def test_send_turn_structured_complete_evaluates_to_done(fake_agent: _FakeAgent) -> None:
    fake_agent.response = _FakeResponse(
        text="implemented",
        structured={
            "complete": True,
            "remaining_work": [],
            "blocked_on": None,
            "summary": "all green",
        },
    )
    gateway = AntigravityAgentGateway(cwd=".")
    outcome = await gateway.send_turn("go")
    await gateway.close()
    result = evaluate(structured=outcome.verdict, output_text=outcome.output_text)
    assert result == Done(summary="all green")
    assert outcome.verdict is not None
    assert "antigravity" not in type(outcome.verdict).__module__


async def test_send_turn_structured_blocked_outranks_complete(fake_agent: _FakeAgent) -> None:
    fake_agent.response = _FakeResponse(
        text="cannot proceed",
        structured={
            "complete": True,
            "remaining_work": [],
            "blocked_on": "needs human for MCP OAuth",
            "summary": "looks done",
        },
    )
    gateway = AntigravityAgentGateway(cwd=".")
    outcome = await gateway.send_turn("go")
    await gateway.close()
    result = evaluate(structured=outcome.verdict, output_text=outcome.output_text)
    assert result == Blocked(reason="needs human for MCP OAuth")


async def test_send_turn_none_structured_falls_back_to_marker(fake_agent: _FakeAgent) -> None:
    fake_agent.response = _FakeResponse(
        text="wrapping up\nAGYLOOP_TASK_FULLY_COMPLETE\n",
        structured=None,
    )
    gateway = AntigravityAgentGateway(cwd=".")
    outcome = await gateway.send_turn("go")
    await gateway.close()
    assert outcome.verdict is None
    result = evaluate(structured=outcome.verdict, output_text=outcome.output_text)
    assert result == Done(summary="")


async def test_send_turn_none_structured_without_marker_is_continue_never_done(
    fake_agent: _FakeAgent,
) -> None:
    fake_agent.response = _FakeResponse(text="still working", structured=None)
    gateway = AntigravityAgentGateway(cwd=".")
    outcome = await gateway.send_turn("go")
    await gateway.close()
    result = evaluate(structured=outcome.verdict, output_text=outcome.output_text)
    assert isinstance(result, Continue)
    assert not isinstance(result, Done)


async def test_gateway_config_wires_finish_tool_schema(fake_agent: _FakeAgent) -> None:
    gateway = AntigravityAgentGateway(cwd=".")
    await gateway.send_turn("go")
    await gateway.close()
    schema_json = fake_agent.config.capabilities.finish_tool_schema_json
    assert schema_json is not None
    parsed = json.loads(schema_json)
    assert "complete" in parsed["properties"]


async def test_resume_failure_degrades_to_fresh_conversation_seeded_with_plan() -> None:
    agents: list[_FakeAgent] = []
    calls = {"n": 0}

    def _factory(config: object) -> _FakeAgent:
        agent = _FakeAgent(config)
        agents.append(agent)
        calls["n"] += 1
        if calls["n"] == 1:
            agent.response = _FakeResponse(
                error=AntigravityExecutionError("conversation not found")
            )
        else:
            agent.response = _FakeResponse(text="resumed from plan")
            agent.conversation_id = "n" * 32
        return agent

    with patch("agyloop.infrastructure.agent.gateway.Agent", side_effect=_factory):
        gateway = AntigravityAgentGateway(
            cwd=".",
            conversation_id="o" * 32,
            plan_seed="- [ ] finish the plan",
        )
        outcome = await gateway.send_turn("Continue exactly where you left off.")
        await gateway.close()

    assert len(agents) == 2
    assert agents[0].config.conversation_id == "o" * 32
    assert agents[1].config.conversation_id is None
    assert "- [ ] finish the plan" in agents[1].prompts[0]
    assert outcome.output_text == "resumed from plan"
    assert outcome.session_id == "n" * 32


async def test_resume_degrades_when_agent_constructor_fails_on_conversation() -> None:
    agents: list[_FakeAgent] = []
    calls = {"n": 0}

    def _factory(config: object) -> _FakeAgent:
        calls["n"] += 1
        if calls["n"] == 1:
            raise AntigravityValidationError("invalid conversation_id")
        agent = _FakeAgent(config)
        agents.append(agent)
        agent.response = _FakeResponse(text="seeded")
        agent.conversation_id = "n" * 32
        return agent

    with patch("agyloop.infrastructure.agent.gateway.Agent", side_effect=_factory):
        gateway = AntigravityAgentGateway(
            cwd=".",
            conversation_id="o" * 32,
            plan_seed="- [ ] finish the plan",
        )
        outcome = await gateway.send_turn("Continue exactly where you left off.")
        await gateway.close()

    assert len(agents) == 1
    assert agents[0].config.conversation_id is None
    assert "- [ ] finish the plan" in agents[0].prompts[0]
    assert outcome.output_text == "seeded"
    assert outcome.session_id == "n" * 32


async def test_resume_degrades_when_session_enter_fails_on_conversation() -> None:
    agents: list[_FakeAgent] = []
    calls = {"n": 0}

    def _factory(config: object) -> _FakeAgent:
        agent = _FakeAgent(config)
        agents.append(agent)
        calls["n"] += 1
        if calls["n"] == 1:

            async def _boom(*_args: object) -> _FakeAgent:
                raise AntigravityExecutionError("conversation not found")

            agent.__aenter__ = _boom  # type: ignore[method-assign]
        else:
            agent.response = _FakeResponse(text="seeded")
            agent.conversation_id = "n" * 32
        return agent

    with patch("agyloop.infrastructure.agent.gateway.Agent", side_effect=_factory):
        gateway = AntigravityAgentGateway(
            cwd=".",
            conversation_id="o" * 32,
            plan_seed="- [ ] finish the plan",
        )
        outcome = await gateway.send_turn("Continue exactly where you left off.")
        await gateway.close()

    assert len(agents) == 2
    assert agents[1].config.conversation_id is None
    assert "- [ ] finish the plan" in agents[1].prompts[0]
    assert outcome.output_text == "seeded"


async def test_resume_degrades_when_chat_validation_error_is_conversation_failure() -> None:
    agents: list[_FakeAgent] = []
    calls = {"n": 0}

    def _factory(config: object) -> _FakeAgent:
        agent = _FakeAgent(config)
        agents.append(agent)
        calls["n"] += 1
        if calls["n"] == 1:
            agent.response = _FakeResponse(error=AntigravityValidationError("conversation expired"))
        else:
            agent.response = _FakeResponse(text="seeded")
            agent.conversation_id = "n" * 32
        return agent

    with patch("agyloop.infrastructure.agent.gateway.Agent", side_effect=_factory):
        gateway = AntigravityAgentGateway(
            cwd=".",
            conversation_id="o" * 32,
            plan_seed="- [ ] finish the plan",
        )
        outcome = await gateway.send_turn("Continue exactly where you left off.")
        await gateway.close()

    assert len(agents) == 2
    assert agents[1].config.conversation_id is None
    assert "- [ ] finish the plan" in agents[1].prompts[0]
    assert outcome.output_text == "seeded"


_WITHDRAWN_LOG = "404 NOT_FOUND models/gemini-2.5-flash-lite is no longer available to new users"


async def test_empty_output_with_harness_404_is_config_error(fake_agent: _FakeAgent) -> None:
    fake_agent.response = _FakeResponse(text="", log_line=_WITHDRAWN_LOG)
    gateway = AntigravityAgentGateway(cwd=".")
    with pytest.raises(AgentConfigError, match="withdrawn|404|NOT_FOUND"):
        await gateway.send_turn("go")
    await gateway.close()


async def test_nonempty_output_ignores_sidecar_404_noise(fake_agent: _FakeAgent) -> None:
    fake_agent.response = _FakeResponse(text="Finished the parser.", log_line=_WITHDRAWN_LOG)
    gateway = AntigravityAgentGateway(cwd=".")
    outcome = await gateway.send_turn("go")
    await gateway.close()
    assert outcome.output_text == "Finished the parser."
