# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""One builder for Agent.create and Agent.resume.

Nothing persists across resume — not the model, not inline MCP servers, not
tools/disallowed_tools, not custom_tools. Both paths call this function so a
resume cannot silently drop safety restrictions.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, cast

from cursor_sdk import (
    AgentDefinition,
    AgentOptions,
    LocalAgentOptions,
    ModelSelection,
    SandboxOptions,
)
from cursor_sdk.types import McpServerConfig, SettingSource

from cursorloop.domain.model_profile import ModelProfile


def _model_selection(profile: ModelProfile) -> ModelSelection:
    """Convert the domain's plain dict into cursor_sdk dataclasses.

    This is the only place ``to_selection_payload()`` meets ``cursor_sdk``.
    Effort (grok / grok-xhigh) and fast are already params on that payload;
    dropping them here would collapse those profiles.
    """
    payload = profile.to_selection_payload()
    return ModelSelection.from_value(cast(Mapping[str, Any], payload))


def build_agent_options(
    *,
    profile: ModelProfile,
    cwd: str,
    dirs: Sequence[str] | None = None,
    setting_sources: Sequence[SettingSource] | None = None,
    tools: Sequence[str] | None = None,
    disallowed_tools: Sequence[str] | None = None,
    sandbox: SandboxOptions | Mapping[str, Any] | None = None,
    mcp_servers: Mapping[str, McpServerConfig] | None = None,
    subagents: Mapping[str, AgentDefinition | Mapping[str, Any]] | None = None,
    mode: str | None = None,
    name: str | None = None,
    auto_review: bool | None = None,
) -> AgentOptions:
    """Build the full option set used by both create and resume."""
    # Hard defaults, not caller choices — even if the signature lists the names.
    del mode, auto_review
    return AgentOptions(
        model=_model_selection(profile),
        name=name,
        local=LocalAgentOptions(
            cwd=cwd,
            dirs=dirs,
            setting_sources=setting_sources,
            sandbox_options=sandbox,
            # auto-review parks on an interactive gate; an unattended run that
            # enables it will stall waiting for a human.
            auto_review=False,
        ),
        mcp_servers=mcp_servers,
        agents=subagents,
        # plan mode is not an unattended executor — it waits on a human to
        # confirm the plan rather than carrying the work through.
        mode="agent",
        tools=tools,
        disallowed_tools=disallowed_tools,
    )
