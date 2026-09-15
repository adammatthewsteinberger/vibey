# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from google.antigravity.types import BuiltinTools

from agyloop.domain.errors import AgentConfigError
from agyloop.infrastructure.agent.options import build_local_config
from agyloop.infrastructure.agent.probe import (
    AntigravityCapacityProbe,
    build_probe_config,
)


class _FakeResponse:
    async def text(self) -> str:
        return "OK"

    async def structured_output(self) -> None:
        return None


class _FakeAgent:
    def __init__(self, config: object) -> None:
        self.config = config
        self.conversation_id = None
        self.prompts: list[str] = []
        self.closed = False

    async def __aenter__(self) -> _FakeAgent:
        return self

    async def __aexit__(self, *args: object) -> None:
        self.closed = True

    async def chat(self, prompt: str) -> _FakeResponse:
        self.prompts.append(prompt)
        return _FakeResponse()


def test_probe_config_has_no_conversation_id() -> None:
    cfg = build_probe_config(cwd=".")
    assert cfg.conversation_id is None


def test_probe_config_forwards_input_detection_override() -> None:
    from agyloop.domain.model_profile import INPUT_DETECTION_MODEL

    cfg = build_probe_config(cwd=".", model="gemini-2.5-flash", api_key="test-key")
    assert cfg.env is not None
    assert cfg.env["AGYLOOP_INPUT_DETECTION_MODEL"] == INPUT_DETECTION_MODEL
    names = [m.name for m in (cfg.models or [])]
    assert INPUT_DETECTION_MODEL in names


def test_probe_config_uses_none_or_read_only_tools() -> None:
    cfg = build_probe_config(cwd=".")
    tools = list(cfg.capabilities.enabled_tools or ())
    allowed = set(BuiltinTools.none()) | set(BuiltinTools.read_only())
    assert set(tools) <= allowed
    assert BuiltinTools.RUN_COMMAND not in tools
    assert cfg.mcp_servers in (None, [])


def test_live_config_pins_empty_mcp_servers_like_probe() -> None:
    """Live SDK session must pin mcp_servers=[] the same as probe (no MCP OAuth)."""
    probe = build_probe_config(cwd=".")
    live = build_local_config(cwd=".")
    assert "mcp_servers" in probe.model_fields_set
    assert probe.mcp_servers == []
    assert "mcp_servers" in live.model_fields_set
    assert live.mcp_servers == []


@pytest.fixture
def fake_probe_agent() -> _FakeAgent:
    agent = _FakeAgent(config=None)

    def _factory(config: object) -> _FakeAgent:
        agent.config = config
        return agent

    with patch("agyloop.infrastructure.agent.probe.Agent", side_effect=_factory):
        yield agent


async def test_probe_issues_single_chat_without_conversation_id(
    fake_probe_agent: _FakeAgent,
) -> None:
    probe = AntigravityCapacityProbe(cwd=".")
    outcome = await probe.probe()
    assert fake_probe_agent.config.conversation_id is None
    assert len(fake_probe_agent.prompts) == 1
    assert fake_probe_agent.closed is True
    assert outcome.session_id is None


class _HarnessDiesOnStartAgent:
    """Reproduces the SDK failure when the local harness exits without writing
    its 4-byte length header."""

    def __init__(self, config: object) -> None:
        self.config = config
        self.exited = False

    async def __aenter__(self) -> _HarnessDiesOnStartAgent:
        raise RuntimeError("Failed to read length from stdout. Stderr: ")

    async def __aexit__(self, *args: object) -> None:
        self.exited = True


@pytest.mark.asyncio
async def test_probe_diagnoses_a_harness_that_dies_on_start(tmp_path) -> None:
    built: list[_HarnessDiesOnStartAgent] = []

    def _factory(config: object) -> _HarnessDiesOnStartAgent:
        agent = _HarnessDiesOnStartAgent(config)
        built.append(agent)
        return agent

    probe = AntigravityCapacityProbe(cwd=str(tmp_path))
    with (
        patch("agyloop.infrastructure.agent.probe.Agent", side_effect=_factory),
        pytest.raises(AgentConfigError) as excinfo,
    ):
        await probe.probe()

    message = str(excinfo.value)
    assert "harness failed to start" in message
    assert "--gateway cli" in message
    assert "Failed to read length from stdout" in message
    # __aexit__ must still run so the orphaned harness Popen is reaped.
    assert built[0].exited is True


@pytest.mark.asyncio
async def test_probe_set_model_and_error_handling(tmp_path: Path) -> None:
    from google.antigravity.types import AntigravityConnectionError, AntigravityValidationError

    probe = AntigravityCapacityProbe(cwd=str(tmp_path), model="gemini-2.5-flash")
    probe.set_model("gemini-2.5-flash-lite")
    assert probe._model == "gemini-2.5-flash-lite"

    # Validation error raises AgentConfigError
    class _ValidationErrAgent:
        def __init__(self, config: object) -> None:
            pass

        async def __aenter__(self) -> _ValidationErrAgent:
            raise AntigravityValidationError("bad validation")

        async def __aexit__(self, *args: object) -> None:
            pass

    with (
        patch(
            "agyloop.infrastructure.agent.probe.Agent",
            side_effect=lambda cfg: _ValidationErrAgent(cfg),
        ),
        pytest.raises(AgentConfigError, match="bad validation"),
    ):
        await probe.probe()

    # Connection error returns outcome from exception
    class _ConnectionErrAgent:
        def __init__(self, config: object) -> None:
            pass

        async def __aenter__(self) -> _ConnectionErrAgent:
            raise AntigravityConnectionError("disconnected")

        async def __aexit__(self, *args: object) -> None:
            pass

    with patch(
        "agyloop.infrastructure.agent.probe.Agent", side_effect=lambda cfg: _ConnectionErrAgent(cfg)
    ):
        outcome = await probe.probe()
        assert outcome.signals.exception_type == "AntigravityConnectionError"
