# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest

from claudeloop.domain.control import (
    SetPermissionModeCommand,
    SlashCommand,
)
from claudeloop.infrastructure.agent.options import build_turn_options
from claudeloop.infrastructure.chat_meta import ChatMetaStore
from claudeloop.infrastructure.control import FileRunControl
from claudeloop.infrastructure.resources.store import RunResourceStore
from claudeloop.infrastructure.tool_approval import ToolApprovalGate


class _FakeContext:
    """Stand-in for ToolPermissionContext — gate ignores the object."""

    suggestions: list[Any] = []


def test_options_default_permission_bypass() -> None:
    options = build_turn_options(cwd="/tmp")
    assert options.permission_mode == "bypassPermissions"


def test_options_skills_plugins_add_dirs() -> None:
    options = build_turn_options(
        cwd="/tmp",
        permission_mode="plan",
        add_dirs=["/extra"],
        skills=["demo-skill"],
        plugins=["/plugins/local"],
        mcp_servers={"demo": {"command": "echo", "args": []}},
    )
    assert options.permission_mode == "plan"
    assert any(str(p) == "/extra" for p in options.add_dirs)
    assert options.skills == ["demo-skill"]
    assert options.plugins
    assert "demo" in options.mcp_servers


def test_resource_store_attach_and_skills(tmp_path: Path) -> None:
    store = RunResourceStore(tmp_path / "resources")
    store.ensure()
    src = tmp_path / "note.txt"
    src.write_text("hi", encoding="utf-8")
    store.attach(src)
    store.add_skill("s1")
    (tmp_path / "extra").mkdir()
    store.add_folder(str(tmp_path / "extra"))
    snap = store.snapshot()
    assert "note.txt" in snap.attachments
    assert "s1" in snap.skills
    assert any(str(tmp_path / "extra") in f for f in snap.folders)


def test_memory_and_artifact_crud(tmp_path: Path) -> None:
    store = RunResourceStore(tmp_path / "resources")
    store.set_memory("prefs", "prefer pytest")
    assert "prefer pytest" in store.get_memory("prefs")
    assert store.list_memories()
    art = tmp_path / "out.bin"
    art.write_bytes(b"abc")
    store.put_artifact("out.bin", art)
    assert "out.bin" in store.list_artifacts()
    store.remove_artifact("out.bin")
    store.remove_memory("prefs")


def test_chat_meta_pin_share(tmp_path: Path) -> None:
    chats = ChatMetaStore(tmp_path / "chats")
    chats.set_pinned("sess-1", True)
    chats.rename("sess-1", "My chat")
    shared = chats.share("sess-1", bundle_dir=tmp_path / "shares")
    assert Path(shared["bundle_path"]).is_file()
    meta = chats.get("sess-1")
    assert meta.pinned is True
    assert meta.alias == "My chat"


def test_control_serializes_permission_and_slash(tmp_path: Path) -> None:
    inbox = FileRunControl(tmp_path / "inbox")
    inbox.enqueue(SetPermissionModeCommand(mode="manual"))
    inbox.enqueue(SlashCommand(text="/status"))
    cmds = inbox.poll()
    assert any(isinstance(c, SetPermissionModeCommand) for c in cmds)
    assert any(isinstance(c, SlashCommand) for c in cmds)


@pytest.mark.asyncio
async def test_tool_approval_timeout_denies() -> None:
    gate = ToolApprovalGate(timeout_seconds=0.05)
    result = await gate.can_use_tool("Bash", {"command": "true"}, _FakeContext())
    assert result.behavior == "deny"


@pytest.mark.asyncio
async def test_tool_approval_allow() -> None:
    gate = ToolApprovalGate(timeout_seconds=2.0)

    async def _decide() -> None:
        await asyncio.sleep(0.05)
        for _ in range(40):
            events = gate.drain_events()
            for event in events:
                if event.get("type") == "tool.approval_needed":
                    gate.resolve(str(event["request_id"]), allow=True)
                    return
            await asyncio.sleep(0.05)

    task = asyncio.create_task(_decide())
    result = await gate.can_use_tool("Read", {"path": "x"}, _FakeContext())
    await task
    assert result.behavior == "allow"


def test_research_start(tmp_path: Path) -> None:
    store = RunResourceStore(tmp_path / "resources")
    path = store.start_research("what is claudeloop")
    assert path.is_file()
    status = store.research_status()
    assert status
    assert status[0]["status"] == "started"
