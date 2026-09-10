# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Contract suite: every AgentGateway implementation speaks the same port."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

from cursorloop.application.ports import AgentGateway
from cursorloop.domain.model_profile import SHIPPED_PRESETS, ModelProfile
from cursorloop.infrastructure.agent.cli_fallback import (
    CliFallbackGateway,
    build_agent_argv,
    parse_stream_json_lines,
)
from cursorloop.infrastructure.agent.gateway import CursorAgentGateway
from cursorloop.infrastructure.agent.scripted import ScriptedAgentGateway, ScriptedTurn
from cursorloop.infrastructure.agent.watchdog import TurnWatchdog
from tests.application import fakes
from tests.fixtures import sdk_payloads
from tests.infrastructure.test_gateway import FakeCursorAgent, FakeRunEventSink


@pytest.fixture
def scripted_gateway() -> ScriptedAgentGateway:
    return ScriptedAgentGateway(
        [
            ScriptedTurn(
                output_text="CURSORLOOP_TASK_FULLY_COMPLETE",
                verdict=None,
            )
        ]
    )


@pytest.fixture
def cli_gateway(tmp_path: Path) -> CliFallbackGateway:
    def fake_runner(argv: list[str]) -> SimpleNamespace:
        assert argv[0] == "agent"
        assert "--force" in argv
        body = (
            '{"type":"assistant","text":"hi\\n"}\n'
            '{"type":"assistant","text":"CURSORLOOP_TASK_FULLY_COMPLETE"}\n'
        )
        return SimpleNamespace(stdout=body, returncode=0)

    return CliFallbackGateway(workspace=tmp_path, runner=fake_runner)


@pytest.fixture
def sdk_gateway() -> CursorAgentGateway:
    clock = fakes.FakeClock()
    return CursorAgentGateway(
        client=object(),
        agent=FakeCursorAgent(run=sdk_payloads.fake_streaming_run(["ok"])),
        profile=SHIPPED_PRESETS["composer"],
        watchdog=TurnWatchdog(
            turn_timeout=timedelta(minutes=30),
            stall_timeout=timedelta(minutes=10),
            clock=clock,
        ),
        event_sink=FakeRunEventSink(),
    )


@pytest.mark.parametrize("gateway_fixture", ["scripted_gateway", "cli_gateway", "sdk_gateway"])
@pytest.mark.asyncio
async def test_gateway_port_contract(gateway_fixture: str, request: pytest.FixtureRequest) -> None:
    gateway: AgentGateway = request.getfixturevalue(gateway_fixture)
    assert isinstance(gateway, AgentGateway)
    assert gateway.agent_id()
    await gateway.set_profile(ModelProfile(model_id="composer-2.5"))
    await gateway.set_cwd(str(Path.cwd()))
    outcome = await gateway.send_turn("do the thing")
    assert outcome.output_text
    assert await gateway.cancel_active_run() in {True, False}
    await gateway.close()


def test_build_agent_argv_never_shell() -> None:
    argv = build_agent_argv(prompt="p", model="composer-2.5", workspace=Path("/tmp/ws"))
    assert argv[0] == "agent"
    assert "-p" in argv
    assert "--force" in argv
    assert "--output-format" in argv
    assert "stream-json" in argv


def test_parse_stream_json_lines_extracts_text() -> None:
    outcome = parse_stream_json_lines(
        [
            '{"type":"assistant","text":"hello "}',
            '{"type":"assistant","text":"world"}',
        ]
    )
    assert "hello" in outcome.output_text
    assert "world" in outcome.output_text
