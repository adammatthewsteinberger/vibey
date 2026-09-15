# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from pathlib import Path

import pytest

from claudeloop import bootstrap_ops
from claudeloop.domain.control import (
    ApproveToolCommand,
    DenyToolCommand,
    PromptDeferredCommand,
    PromptNowCommand,
    ResourceMutateCommand,
    ResponseFeedbackCommand,
    ResponseRetryCommand,
    SetCwdCommand,
    SetEffortCommand,
    SetModelCommand,
    SetPermissionModeCommand,
    SetPresetCommand,
    SlashCommand,
    StopCommand,
)
from claudeloop.infrastructure.agent.options import build_turn_options
from claudeloop.infrastructure.control import FileRunControl
from claudeloop.infrastructure.github_import import (
    ImportedIssue,
    materialize_issue_attachment,
    parse_issue_ref,
    parse_repo_ref,
)
from claudeloop.infrastructure.resources.adapter import ResourcePortAdapter
from claudeloop.infrastructure.resources.store import RunResourceStore
from claudeloop.infrastructure.rundir import RunDirectory, runs_root_for


@pytest.mark.parametrize(
    "command",
    [
        StopCommand(),
        PromptNowCommand(text="now"),
        PromptDeferredCommand(text="later"),
        SetModelCommand(model="high"),
        SetEffortCommand(effort="max"),
        SetPresetCommand(preset="low"),
        SetPermissionModeCommand(mode="manual"),
        SetCwdCommand(path="/tmp/work"),
        SlashCommand(text="/status"),
        ApproveToolCommand(request_id="r1"),
        DenyToolCommand(request_id="r2", reason="nope"),
        ResourceMutateCommand(action="add", kind="skill", value="s1"),
        ResponseFeedbackCommand(verdict="bad", note="x"),
        ResponseRetryCommand(),
    ],
)
def test_file_run_control_roundtrip_all_commands(tmp_path: Path, command: object) -> None:
    inbox = FileRunControl(tmp_path / "inbox")
    inbox.enqueue(command)  # type: ignore[arg-type]
    got = inbox.poll()
    assert len(got) == 1
    assert type(got[0]) is type(command)
    assert got[0] == command


def test_options_can_use_tool_only_for_manual() -> None:
    async def _cb(name: str, tool_input: dict, ctx: object) -> object:  # noqa: ANN001
        del name, tool_input, ctx
        raise AssertionError("unused")

    bypass = build_turn_options(cwd="/tmp", permission_mode="bypass", can_use_tool=_cb)
    assert bypass.can_use_tool is None
    manual = build_turn_options(cwd="/tmp", permission_mode="manual", can_use_tool=_cb)
    assert manual.can_use_tool is _cb
    assert manual.permission_mode == "default"


def test_parse_github_refs() -> None:
    assert parse_issue_ref("acme/widgets#42") == ("acme", "widgets", 42)
    with pytest.raises(ValueError):
        parse_issue_ref("not-an-issue")
    assert parse_repo_ref("acme/widgets@main") == ("acme", "widgets", "main")
    assert parse_repo_ref("acme/widgets") == ("acme", "widgets", None)
    with pytest.raises(ValueError):
        parse_repo_ref("solo")


def test_materialize_issue_attachment(tmp_path: Path) -> None:
    issue = ImportedIssue(
        owner="o",
        repo="r",
        number=1,
        title="T",
        body="Body",
        url="https://github.com/o/r/issues/1",
    )
    path = materialize_issue_attachment(issue, tmp_path)
    assert path.is_file()
    assert "Body" in path.read_text(encoding="utf-8")


def test_resource_port_adapter_mutate_paths(tmp_path: Path) -> None:
    store = RunResourceStore(tmp_path / "resources")
    adapter = ResourcePortAdapter(store)
    src = tmp_path / "a.txt"
    src.write_text("x", encoding="utf-8")
    adapter.apply_mutate(action="add", kind="attachment", value=str(src))
    adapter.apply_mutate(action="add", kind="folder", value=str(tmp_path))
    adapter.apply_mutate(action="add", kind="skill", value="sk")
    adapter.apply_mutate(action="add", kind="plugin", value="/plugins/p")
    adapter.apply_mutate(
        action="set",
        kind="connector",
        value='{"command":"echo"}',
        name="echo",
    )
    adapter.apply_mutate(action="add", kind="github", value="o/r@main")
    adapter.apply_mutate(action="set", kind="memory", value="remember this", name="prefs")
    adapter.apply_mutate(action="add", kind="web-search", value="on")
    adapter.apply_mutate(action="add", kind="research", value="what is x")
    payload = adapter.gateway_payload()
    assert payload["skills"] == ["sk"]
    assert payload["plugins"] == ["/plugins/p"]
    assert payload["mcp_servers"]
    assert "WebSearch" in (payload.get("allowed_tools") or [])
    assert "remember this" in (payload.get("system_prompt_append") or "")
    adapter.apply_mutate(action="rm", kind="skill", value="sk")
    adapter.apply_mutate(action="rm", kind="attachment", value="a.txt")
    assert "a.txt" not in store.snapshot().attachments


def test_bootstrap_ops_enqueue_and_memory(tmp_path: Path) -> None:
    run_dir = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    run_id = run_dir.read_meta().run_id
    assert (
        bootstrap_ops.enqueue_permission_mode(tmp_path, "plan", run_id=run_id).command_type
        == "set_permission_mode"
    )
    assert (
        bootstrap_ops.enqueue_cwd(tmp_path, str(tmp_path), run_id=run_id).command_type == "set_cwd"
    )
    assert bootstrap_ops.enqueue_slash(tmp_path, "/status", run_id=run_id).command_type == "slash"
    assert (
        bootstrap_ops.enqueue_tool_decision(
            tmp_path, "rid", allow=False, reason="x", run_id=run_id
        ).command_type
        == "deny_tool"
    )
    assert (
        bootstrap_ops.enqueue_resource(
            tmp_path, action="add", kind="skill", value="s", run_id=run_id
        ).command_type
        == "resource_mutate"
    )
    assert (
        bootstrap_ops.enqueue_response_feedback(
            tmp_path, "good", note="n", run_id=run_id
        ).command_type
        == "response_feedback"
    )
    assert (
        bootstrap_ops.enqueue_response_retry(tmp_path, run_id=run_id).command_type
        == "response_retry"
    )
    bootstrap_ops.memory_set(tmp_path, "note", "hello", run_id=run_id)
    assert bootstrap_ops.memory_get(tmp_path, "note", run_id=run_id) == "hello"
    assert bootstrap_ops.memory_list(tmp_path, run_id=run_id)
    bootstrap_ops.memory_rm(tmp_path, "note", run_id=run_id)
    art = tmp_path / "out.txt"
    art.write_text("z", encoding="utf-8")
    bootstrap_ops.artifact_put(tmp_path, "out.txt", art, run_id=run_id)
    assert "out.txt" in bootstrap_ops.artifact_list(tmp_path, run_id=run_id)
    bootstrap_ops.chat_pin(tmp_path, "sess-1")
    bootstrap_ops.chat_rename(tmp_path, "sess-1", "Alias")
    shared = bootstrap_ops.chat_share(tmp_path, "sess-1")
    assert "bundle_path" in shared
    assert bootstrap_ops.chat_show(tmp_path, "sess-1")["pinned"] is True
