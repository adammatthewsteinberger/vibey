# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Autonomy switch for LocalAgentConfig — never block on a human."""

from __future__ import annotations

import json

from google.antigravity.hooks import policy
from google.antigravity.types import BuiltinTools, CustomSystemInstructions
from google.antigravity.utils.interactive import AskQuestionHook, ToolConfirmationHook

from agyloop.domain.completion import DEFAULT_DONE_MARKER
from agyloop.infrastructure.agent.options import build_local_config
from agyloop.infrastructure.agent.policies import (
    config_has_allow_all,
    config_has_nonblocking_policies,
)


def test_local_config_pins_empty_mcp_servers() -> None:
    cfg = build_local_config(cwd=".")
    assert "mcp_servers" in cfg.model_fields_set
    assert cfg.mcp_servers == []


def test_strict_autonomy_disables_ask_question_tool() -> None:
    cfg = build_local_config(cwd=".", strict_autonomy=True)
    assert BuiltinTools.ASK_QUESTION in (cfg.capabilities.disabled_tools or [])


def test_local_config_is_autonomous():
    cfg = build_local_config(cwd=".")
    assert config_has_allow_all(cfg) or config_has_nonblocking_policies(cfg)


def test_local_config_attaches_allow_all() -> None:
    cfg = build_local_config(cwd=".")
    assert config_has_allow_all(cfg)
    assert any(p.name == "allow_all" for p in cfg.policies)


def test_scoped_mode_omits_allow_all() -> None:
    cfg = build_local_config(cwd=".", permission_mode="scoped")
    assert not config_has_allow_all(cfg)
    names = {p.name for p in cfg.policies}
    assert "workspace_only" in names


def test_local_config_never_uses_ask_user_blocking_handler() -> None:
    cfg = build_local_config(cwd=".")
    assert config_has_nonblocking_policies(cfg)
    for item in cfg.policies:
        assert item.decision != policy.Decision.ASK_USER


def test_local_config_never_registers_interactive_hooks() -> None:
    cfg = build_local_config(cwd=".")
    for hook in cfg.hooks:
        assert not isinstance(hook, (ToolConfirmationHook, AskQuestionHook))
        assert "utils.interactive" not in type(hook).__module__


def test_local_config_uses_additive_system_instructions() -> None:
    cfg = build_local_config(cwd=".")
    assert not isinstance(cfg.system_instructions, CustomSystemInstructions)
    normalized = cfg._get_system_instructions()
    assert normalized is not None
    assert not isinstance(normalized, CustomSystemInstructions)


def test_local_config_scopes_workspace_and_denies_destructive_commands() -> None:
    cfg = build_local_config(cwd=".")
    names = {p.name for p in cfg.policies}
    assert "workspace_only" in names
    assert any("destructive" in (p.name or "") for p in cfg.policies)


def _schema_properties(schema: object) -> set[str]:
    if isinstance(schema, str):
        parsed: object = json.loads(schema)
    else:
        parsed = schema
    assert isinstance(parsed, dict)
    properties = parsed.get("properties")
    assert isinstance(properties, dict)
    return set(properties)


def test_local_config_wires_finish_tool_schema_json() -> None:
    cfg = build_local_config(cwd=".")
    schema_json = cfg.capabilities.finish_tool_schema_json
    assert schema_json is not None
    fields = _schema_properties(schema_json)
    assert fields >= {"complete", "remaining_work", "blocked_on", "summary"}


def test_local_config_wires_response_schema() -> None:
    cfg = build_local_config(cwd=".")
    schema = cfg.response_schema
    assert schema is not None
    fields = _schema_properties(schema)
    assert fields >= {"complete", "remaining_work", "blocked_on", "summary"}


def test_completion_schema_declares_strict_field_types() -> None:
    cfg = build_local_config(cwd=".")
    schema = cfg.response_schema
    if isinstance(schema, str):
        schema = json.loads(schema)
    assert isinstance(schema, dict)
    properties = schema["properties"]
    assert isinstance(properties, dict)
    assert properties["complete"] == {
        "type": "boolean",
        "description": "True only when the entire task is finished.",
    }
    assert properties["remaining_work"]["items"] == {"type": "string"}
    assert properties["blocked_on"]["type"] == ["string", "null"]
    assert properties["summary"]["type"] == "string"
    assert set(schema["required"]) == set(properties)
    assert schema["additionalProperties"] is False


def test_safe_mode_still_wires_finish_tool_schema() -> None:
    cfg = build_local_config(cwd=".", permission_mode="safe")
    assert cfg.capabilities.finish_tool_schema_json is not None
    fields = _schema_properties(cfg.capabilities.finish_tool_schema_json)
    assert "complete" in fields


def test_local_config_appends_done_marker_as_fallback_instruction() -> None:
    cfg = build_local_config(cwd=".")
    rendered = cfg._get_system_instructions()
    text = str(rendered)
    assert DEFAULT_DONE_MARKER in text


def test_local_config_forwards_input_detection_override() -> None:
    from agyloop.domain.model_profile import INPUT_DETECTION_MODEL

    cfg = build_local_config(cwd=".", model="gemini-2.5-flash", api_key="test-key")
    assert cfg.env is not None
    assert cfg.env["AGYLOOP_INPUT_DETECTION_MODEL"] == INPUT_DETECTION_MODEL
    names = [m.name for m in (cfg.models or [])]
    assert "gemini-2.5-flash" in names
    assert INPUT_DETECTION_MODEL in names


def test_local_config_with_system_prompt_append() -> None:
    cfg = build_local_config(cwd=".", system_prompt_append="extra domain guidelines")
    rendered = str(cfg._get_system_instructions())
    assert "extra domain guidelines" in rendered


def test_safe_mode_with_strict_autonomy() -> None:
    cfg = build_local_config(cwd=".", permission_mode="safe", strict_autonomy=True)
    assert cfg.capabilities.enabled_tools is not None
    assert BuiltinTools.ASK_QUESTION not in cfg.capabilities.enabled_tools
