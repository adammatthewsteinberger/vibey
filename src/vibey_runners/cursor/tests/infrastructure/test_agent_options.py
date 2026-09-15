# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from cursor_sdk import AgentDefinition, ModelSelection, SandboxOptions, StdioMcpServerConfig

from cursorloop.domain.model_profile import SHIPPED_PRESETS
from cursorloop.infrastructure.agent.options import build_agent_options


def test_auto_review_is_always_off_for_autonomous_runs() -> None:
    """Auto-review routes local tool calls through an interactive gate. An
    unattended run that enables it will park."""
    options = build_agent_options(profile=SHIPPED_PRESETS["composer"], cwd="/repo")
    assert options.local is not None
    assert options.local.auto_review is False


def test_caller_cannot_enable_auto_review() -> None:
    """auto_review is a hard default, not a caller choice — even True parks."""
    options = build_agent_options(
        profile=SHIPPED_PRESETS["composer"], cwd="/repo", auto_review=True
    )
    assert options.local is not None
    assert options.local.auto_review is False


def test_mode_is_explicitly_agent_never_plan() -> None:
    options = build_agent_options(profile=SHIPPED_PRESETS["composer"], cwd="/repo")
    assert options.mode == "agent"


def test_caller_cannot_switch_to_plan_mode() -> None:
    """Plan mode is not an unattended executor; the builder ignores the arg."""
    options = build_agent_options(profile=SHIPPED_PRESETS["composer"], cwd="/repo", mode="plan")
    assert options.mode == "agent"


def test_hermetic_by_default_no_setting_sources() -> None:
    """Without setting_sources, only inline MCP servers load — and the same
    switch gates project skills. Hermetic is the reproducible default;
    --setting-sources project is an opt-in that also enables project MCP."""
    options = build_agent_options(profile=SHIPPED_PRESETS["composer"], cwd="/repo")
    assert options.local is not None
    assert options.local.setting_sources is None


def test_model_selection_carries_profile_params() -> None:
    options = build_agent_options(profile=SHIPPED_PRESETS["composer-fast"], cwd="/repo")
    assert isinstance(options.model, ModelSelection)
    assert options.model.id == "composer-2.5"
    assert [(p.id, p.value) for p in options.model.params] == [("fast", "true")]


def test_grok_effort_survives_model_selection_mapping() -> None:
    """Grok identity lives in ModelProfile.effort. Dropping effort when mapping
    to ModelSelection collapses grok and grok-xhigh into the same selection."""
    grok = build_agent_options(profile=SHIPPED_PRESETS["grok"], cwd="/repo")
    xhigh = build_agent_options(profile=SHIPPED_PRESETS["grok-xhigh"], cwd="/repo")
    assert isinstance(grok.model, ModelSelection)
    assert grok.model.id == "cursor-grok-4.6"
    assert [(p.id, p.value) for p in grok.model.params] == [("effort", "high")]
    assert [(p.id, p.value) for p in xhigh.model.params] == [("effort", "xhigh")]
    assert grok.model != xhigh.model


def test_multi_root_goes_to_dirs_not_cwd() -> None:
    """LocalAgentOptions rejects multi-entry cwd; extra roots belong in dirs."""
    options = build_agent_options(
        profile=SHIPPED_PRESETS["composer"], cwd="/repo", dirs=("/repo/pkg-a", "/repo/pkg-b")
    )
    assert options.local is not None
    assert options.local.cwd == "/repo"
    assert list(options.local.dirs) == ["/repo/pkg-a", "/repo/pkg-b"]


def test_resume_uses_the_same_builder_and_loses_nothing() -> None:
    """Nothing persists across Agent.resume(): not the model, not inline MCP,
    not tools/disallowed_tools. Both paths must produce identical options."""
    kwargs = {
        "profile": SHIPPED_PRESETS["grok"],
        "cwd": "/repo",
        "disallowed_tools": ("shell",),
        "tools": ("read", "edit", "grep"),
    }
    assert build_agent_options(**kwargs) == build_agent_options(**kwargs)


def test_resume_reapplies_mcp_sandbox_subagents_and_name() -> None:
    """A resume path that rebuilds options by hand silently drops these."""
    kwargs = {
        "profile": SHIPPED_PRESETS["grok"],
        "cwd": "/repo",
        "dirs": ("/extra",),
        "setting_sources": ("project",),
        "tools": ("read", "edit"),
        "disallowed_tools": ("shell",),
        "sandbox": SandboxOptions(enabled=True),
        "mcp_servers": {"docs": StdioMcpServerConfig(command="docs-mcp")},
        "subagents": {
            "reviewer": AgentDefinition(description="reviews", prompt="review the diff"),
        },
        "name": "cursorloop/run-1",
    }
    created = build_agent_options(**kwargs)
    resumed = build_agent_options(**kwargs)
    assert created == resumed
    assert created.name == "cursorloop/run-1"
    assert created.mcp_servers == kwargs["mcp_servers"]
    assert created.agents == kwargs["subagents"]
    assert created.tools == kwargs["tools"]
    assert created.disallowed_tools == kwargs["disallowed_tools"]
    assert created.local is not None
    assert created.local.sandbox_options == kwargs["sandbox"]
    assert list(created.local.setting_sources) == ["project"]
    assert list(created.local.dirs) == ["/extra"]
    assert isinstance(created.model, ModelSelection)
    assert [(p.id, p.value) for p in created.model.params] == [("effort", "high")]
