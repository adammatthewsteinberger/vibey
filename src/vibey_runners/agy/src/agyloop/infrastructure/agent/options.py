# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Build ``LocalAgentConfig`` for unattended Antigravity SDK sessions.

Additive ``system_instructions`` only — never ``CustomSystemInstructions``
(F5.2). ``autonomous`` includes ``allow_all()`` plus workspace/destructive
scopes; ``scoped`` / ``safe`` omit ``allow_all``; ``yolo`` is unrestricted.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

from google.antigravity import LocalAgentConfig
from google.antigravity.types import (
    BuiltinTools,
    CapabilitiesConfig,
    SystemInstructionSection,
    TemplatedSystemInstructions,
)

from agyloop.domain.completion import (
    COMPLETION_RESPONSE_SCHEMA,
    DONE_MARKER_INSTRUCTION,
)
from agyloop.domain.permission import (
    DEFAULT_USER_PERMISSION_MODE,
    UserPermissionMode,
)
from agyloop.infrastructure.agent.autonomy import (
    AUTONOMY_SYSTEM_PROMPT_FRAGMENT,
    autonomy_hooks,
    build_autonomy_policies,
)
from agyloop.infrastructure.agent.harness_retarget import (
    input_detection_env,
    input_detection_models,
)


def _additive_system_instructions(system_prompt_append: str = "") -> TemplatedSystemInstructions:
    content = f"{AUTONOMY_SYSTEM_PROMPT_FRAGMENT}\n\n{DONE_MARKER_INSTRUCTION}"
    extra = system_prompt_append.strip()
    if extra:
        content = f"{content}\n\n{extra}"
    return TemplatedSystemInstructions(
        sections=[SystemInstructionSection(content=content, title="agyloop_autonomy")]
    )


def _finish_tool_schema_json() -> str:
    return json.dumps(COMPLETION_RESPONSE_SCHEMA)


def _capabilities_for(
    permission_mode: UserPermissionMode,
    *,
    strict_autonomy: bool = False,
) -> CapabilitiesConfig:
    schema_json = _finish_tool_schema_json()
    if permission_mode == "safe":
        tools = list(BuiltinTools.nondestructive())
        if strict_autonomy:
            tools = [tool for tool in tools if tool != BuiltinTools.ASK_QUESTION]
        return CapabilitiesConfig(
            enabled_tools=tools,
            finish_tool_schema_json=schema_json,
        )
    if strict_autonomy:
        return CapabilitiesConfig(
            disabled_tools=[BuiltinTools.ASK_QUESTION],
            finish_tool_schema_json=schema_json,
        )
    return CapabilitiesConfig(finish_tool_schema_json=schema_json)


def build_local_config(
    *,
    cwd: str,
    conversation_id: str | None = None,
    model: str | None = None,
    permission_mode: UserPermissionMode = DEFAULT_USER_PERMISSION_MODE,
    add_dirs: Sequence[str] | None = None,
    system_prompt_append: str = "",
    api_key: str | None = None,
    strict_autonomy: bool = False,
) -> LocalAgentConfig:
    """Construct a headless, autonomous ``LocalAgentConfig``.

    Does not require a key at construction time; bootstrap passes
    ``GOOGLE_API_KEY`` or ``GEMINI_API_KEY`` as ``api_key``. The SDK also
    reads ``GEMINI_API_KEY`` itself if ``api_key`` is unset.
    """
    workspace = str(Path(cwd).resolve())
    extra_dirs = [str(Path(path).resolve()) for path in (add_dirs or ())]
    extra_models = input_detection_models(chat_model=model, api_key=api_key)
    return LocalAgentConfig(
        system_instructions=_additive_system_instructions(system_prompt_append),
        capabilities=_capabilities_for(permission_mode, strict_autonomy=strict_autonomy),
        policies=build_autonomy_policies(
            cwd=workspace,
            add_dirs=extra_dirs,
            permission_mode=permission_mode,
        ),
        hooks=autonomy_hooks(),
        workspaces=[workspace, *extra_dirs],
        conversation_id=conversation_id,
        model=None,
        models=extra_models if model else None,
        env=input_detection_env(),
        api_key=api_key,
        response_schema=COMPLETION_RESPONSE_SCHEMA,
        mcp_servers=[],
    )
