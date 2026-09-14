# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Builds ClaudeAgentOptions for real turns and for the throwaway capacity probe.

Key choices, each tied to an ADR:
- permission_mode defaults to "bypassPermissions" — required for autonomy and so
  mid-run switches can return to bypass (SDK forbids escalating *into* bypass
  unless the session started there). The Python SDK has no
  dangerously_skip_permissions field; this is its equivalent.
- output_format carries the completion verdict JSON schema (see translate.py).
- CLAUDE_CODE_RETRY_WATCHDOG is NOT set by default — see ADR 0005.
- max_buffer_size defaults above the SDK's 1MB floor so large tool results
  (big file reads, base64 blobs) don't abort the run — see
  anthropics/claude-agent-sdk-python#98.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, Literal, cast

from claude_agent_sdk import ClaudeAgentOptions
from claude_agent_sdk.types import (
    PermissionResultAllow,
    PermissionResultDeny,
    SdkPluginConfig,
    ToolPermissionContext,
)

from claudeloop.domain.permission import (
    DEFAULT_USER_PERMISSION_MODE,
    UserPermissionMode,
    to_sdk_permission_mode,
)
from claudeloop.infrastructure.agent.autonomy import (
    AUTONOMY_SYSTEM_PROMPT_FRAGMENT,
    build_hooks,
)
from claudeloop.infrastructure.agent.translate import COMPLETION_OUTPUT_SCHEMA

# 50 MiB — large enough for typical e2e / corpus work; override via config/CLI.
DEFAULT_MAX_BUFFER_SIZE = 50 * 1024 * 1024

EffortOpt = Literal["low", "medium", "high", "xhigh", "max"]

CanUseTool = Callable[
    [str, dict[str, Any], ToolPermissionContext],
    Awaitable[PermissionResultAllow | PermissionResultDeny],
]


def build_turn_options(
    *,
    cwd: str,
    session_id: str | None = None,
    resume: str | None = None,
    continue_conversation: bool = False,
    max_turns: int | None = None,
    max_budget_usd: float | None = None,
    retry_watchdog: bool = False,
    model: str | None = None,
    effort: str | None = None,
    max_buffer_size: int | None = None,
    include_partial_messages: bool = False,
    permission_mode: UserPermissionMode = DEFAULT_USER_PERMISSION_MODE,
    add_dirs: list[str] | None = None,
    skills: list[str] | Literal["all"] | None = None,
    plugins: list[str] | None = None,
    mcp_servers: dict[str, Any] | None = None,
    can_use_tool: CanUseTool | None = None,
    system_prompt_append: str = "",
    allowed_tools: list[str] | None = None,
) -> ClaudeAgentOptions:
    env: dict[str, str] = {"CLAUDE_CODE_MAX_RETRIES": "10"}
    if retry_watchdog:
        env["CLAUDE_CODE_RETRY_WATCHDOG"] = "1"

    append = AUTONOMY_SYSTEM_PROMPT_FRAGMENT
    if system_prompt_append.strip():
        append = f"{append}\n\n{system_prompt_append.strip()}"

    sdk_plugins: list[SdkPluginConfig] = []
    for plugin in plugins or []:
        # Local path plugins vs marketplace names — pass as type=local when path-like.
        if plugin.startswith("/") or plugin.startswith(".") or "/" in plugin:
            sdk_plugins.append({"type": "local", "path": plugin})
        else:
            sdk_plugins.append({"type": "local", "path": plugin})

    # ClaudeAgentOptions.session_id pins a *new* conversation id. The CLI
    # rejects combining it with --resume / --continue unless --fork-session
    # is also set (see claude_agent_sdk.types.ClaudeAgentOptions.session_id).
    # claudeloop resume passes the id both for bookkeeping and as resume=;
    # only resume must reach the SDK options.
    effective_session_id = None if (resume or continue_conversation) else session_id

    sdk_mode = to_sdk_permission_mode(permission_mode)
    kwargs: dict[str, Any] = {
        "cwd": cwd,
        "session_id": effective_session_id,
        "resume": resume,
        "continue_conversation": continue_conversation,
        "permission_mode": sdk_mode,
        "hooks": build_hooks(),
        "system_prompt": {
            "type": "preset",
            "preset": "claude_code",
            "append": append,
        },
        "output_format": {"type": "json_schema", "schema": COMPLETION_OUTPUT_SCHEMA},
        "max_turns": max_turns,
        "max_budget_usd": max_budget_usd,
        "model": model,
        "effort": cast(EffortOpt | None, effort),
        "env": env,
        "max_buffer_size": (
            DEFAULT_MAX_BUFFER_SIZE if max_buffer_size is None else max_buffer_size
        ),
        "include_partial_messages": include_partial_messages,
        "add_dirs": [Path(p) if not isinstance(p, Path) else p for p in (add_dirs or [])],
    }
    if skills is not None:
        kwargs["skills"] = skills
    if sdk_plugins:
        kwargs["plugins"] = sdk_plugins
    if mcp_servers:
        kwargs["mcp_servers"] = mcp_servers
    if can_use_tool is not None and permission_mode == "manual":
        kwargs["can_use_tool"] = can_use_tool
    if allowed_tools:
        kwargs["allowed_tools"] = allowed_tools

    return ClaudeAgentOptions(**kwargs)


def build_probe_options(
    *,
    cwd: str,
    resume: str | None = None,
    max_buffer_size: int | None = None,
    model: str | None = None,
) -> ClaudeAgentOptions:
    """Deliberately minimal: one throwaway turn purely to re-check capacity.
    No CLAUDE.md, no tools, no persisted transcript. See
    docs/architecture/decisions/0004-adaptive-waiting-with-probes-not-sleep.md.

    ``model`` should match the run's active model so a spend-limit on Fable
    (or similar) is not masked by a default-model probe succeeding.
    """
    kwargs: dict[str, Any] = {
        "cwd": cwd,
        "resume": resume,
        "permission_mode": "bypassPermissions",
        "hooks": build_hooks(),
        "setting_sources": None,
        "tools": [],
        "max_turns": 1,
        "extra_args": {"no-session-persistence": None},
        "max_buffer_size": (
            DEFAULT_MAX_BUFFER_SIZE if max_buffer_size is None else max_buffer_size
        ),
    }
    if model:
        kwargs["model"] = model
    return ClaudeAgentOptions(**kwargs)
