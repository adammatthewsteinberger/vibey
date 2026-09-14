# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

import pytest
from cursor_sdk import ModelSelection

from cursorloop.domain.model_profile import SHIPPED_PRESETS
from cursorloop.infrastructure.agent.probe import CursorCapacityProbe, build_probe_options
from tests.fixtures import sdk_payloads


def test_probe_offers_no_tools_at_all() -> None:
    """tools=[] is documented as offering no built-in tools: the model can only
    respond with text. Cheapest possible capacity check, zero blast radius."""
    options = build_probe_options(cwd="/repo")
    assert list(options.tools) == []


def test_probe_is_hermetic_and_leaves_no_transcript() -> None:
    """Agent.prompt() creates, sends, waits, and disposes, so the throwaway
    turn never pollutes the working agent's conversation."""
    options = build_probe_options(cwd="/repo")
    assert options.local is not None
    assert options.local.setting_sources is None
    assert options.name == "cursorloop-probe"


def test_probe_keeps_hard_defaults_auto_review_off_and_mode_agent() -> None:
    options = build_probe_options(cwd="/repo")
    assert options.local is not None
    assert options.local.auto_review is False
    assert options.mode == "agent"


def test_probe_options_preserve_grok_effort() -> None:
    options = build_probe_options(cwd="/repo", profile=SHIPPED_PRESETS["grok"])
    assert isinstance(options.model, ModelSelection)
    assert options.model.id == "cursor-grok-4.6"
    assert [(p.id, p.value) for p in options.model.params] == [("effort", "high")]


async def test_probe_translates_a_finished_prompt_result() -> None:
    def prompt(message: object, options: object, **kwargs: object) -> object:
        del options, kwargs
        assert message == "ok"
        return sdk_payloads.fake_run(status="finished", result="ok", total_tokens=3)

    probe = CursorCapacityProbe("/repo", SHIPPED_PRESETS["composer"], prompt=prompt)
    outcome = await probe.probe()
    assert outcome.signals.run_status == "finished"
    assert outcome.output_text == "ok"
    assert outcome.tokens == 3
    assert outcome.cost_usd is None
    assert outcome.cost_pending is True


async def test_probe_catches_cursor_agent_errors_into_signals() -> None:
    exc = sdk_payloads.fake_rate_limit_error(
        code="usage_limit_reached", is_retryable=False, status_code=402
    )

    def prompt(message: object, options: object, **kwargs: object) -> object:
        del message, options, kwargs
        raise exc

    probe = CursorCapacityProbe("/repo", SHIPPED_PRESETS["composer"], prompt=prompt)
    outcome = await probe.probe()
    assert outcome.signals.error_type == "RateLimitError"
    assert outcome.signals.error_code == "usage_limit_reached"
    assert outcome.signals.http_status == 402
    assert outcome.verdict is None


async def test_probe_unexpected_errors_propagate() -> None:
    def prompt(message: object, options: object, **kwargs: object) -> object:
        del message, options, kwargs
        raise RuntimeError("bridge down")

    probe = CursorCapacityProbe("/repo", SHIPPED_PRESETS["composer"], prompt=prompt)
    with pytest.raises(RuntimeError, match="bridge down"):
        await probe.probe()


async def test_streamed_probe_surfaces_status_error_text() -> None:
    run = sdk_payloads.fake_run(
        status="error",
        result="",
        messages=(
            sdk_payloads.fake_status_message(
                status="ERROR",
                message="You're out of usage. Switch to Auto.",
            ),
        ),
    )
    agent = type(
        "ProbeAgent",
        (),
        {
            "send": lambda self, message, *a, **k: run,
            "close": lambda self: None,
        },
    )()

    probe = CursorCapacityProbe(
        "/repo",
        SHIPPED_PRESETS["composer"],
        create_agent=lambda **kwargs: agent,
        use_streamed_probe=True,
    )
    outcome = await probe.probe()
    assert outcome.signals.run_status == "error"
    assert "out of usage" in outcome.signals.result_text.lower()
    assert outcome.output_text == ""
