# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from collections.abc import AsyncIterator, Sequence
from pathlib import Path

import pytest

from qwenloop.application.runner import (
    AutonomousRunner,
    _trim_transcript,
    _truncate_tool_result,
)
from qwenloop.domain.model import Backend, ChatChunk, ChatMessage, RunStatus, ServerInfo
from qwenloop.infrastructure.profiles import PORTABLE
from qwenloop.infrastructure.run_store import FileRunStore
from qwenloop.infrastructure.tools import SandboxTools


class FakeServer:
    chunks: list[ChatChunk] | None = None

    def inspect(self, profile):  # type: ignore[no-untyped-def]
        return None

    async def install(self, profile):  # type: ignore[no-untyped-def]
        raise AssertionError

    async def start(self, profile):  # type: ignore[no-untyped-def]
        raise AssertionError

    async def health(self, info):  # type: ignore[no-untyped-def]
        return True

    async def stop(self, info):  # type: ignore[no-untyped-def]
        return None

    async def chat_stream(
        self, info: ServerInfo, messages: Sequence[ChatMessage]
    ) -> AsyncIterator[ChatChunk]:
        del info, messages
        chunks = self.chunks or [
            ChatChunk(
                tool_call={
                    "name": "write_file",
                    "arguments": {"path": "done.txt", "content": "ok"},
                }
            ),
            ChatChunk(
                text="```qwenloop-verdict\npass\n```\nQWENLOOP_TASK_FULLY_COMPLETE",
                output_tokens=4,
            ),
        ]
        for chunk in chunks:
            yield chunk


def test_truncate_tool_result_leaves_short_text_untouched() -> None:
    assert _truncate_tool_result("short") == "short"


def test_truncate_tool_result_truncates_long_text() -> None:
    text = "x" * 8_010
    result = _truncate_tool_result(text, limit=8_000)
    assert result.startswith("x" * 8_000)
    assert result.endswith("...[truncated 10 characters]")


def test_trim_transcript_noop_within_budget() -> None:
    transcript = [ChatMessage("system", "sys"), ChatMessage("user", "plan")]
    assert _trim_transcript(transcript, context_window=32_768) is transcript


def test_trim_transcript_never_drops_head_even_over_budget() -> None:
    transcript = [ChatMessage("system", "sys"), ChatMessage("user", "plan")]
    assert _trim_transcript(transcript, context_window=1) is transcript


def test_trim_transcript_drops_oldest_tail_and_marks_it() -> None:
    transcript = [
        ChatMessage("system", "sys"),
        ChatMessage("user", "plan"),
        ChatMessage("tool", "a" * 400),  # 100 estimated tokens, dropped first
        ChatMessage("tool", "b" * 400),  # 100 estimated tokens, dropped second
        ChatMessage("tool", "c" * 4),  # 1 estimated token, kept
    ]
    trimmed = _trim_transcript(transcript, context_window=100)
    assert trimmed[0] == transcript[0]
    assert trimmed[1] == transcript[1]
    assert trimmed[2].role == "system"
    assert "2 earlier turn(s) omitted to fit the 100-token context window" in trimmed[2].content
    assert trimmed[3] == transcript[4]
    assert len(trimmed) == 4


class ScriptedServer:
    """A FakeServer variant that yields a different, pre-scripted turn each call."""

    def __init__(self, turns: list[list[ChatChunk]]) -> None:
        self._turns = turns
        self.seen: list[list[ChatMessage]] = []

    def inspect(self, profile):  # type: ignore[no-untyped-def]
        return None

    async def install(self, profile):  # type: ignore[no-untyped-def]
        raise AssertionError

    async def start(self, profile):  # type: ignore[no-untyped-def]
        raise AssertionError

    async def health(self, info):  # type: ignore[no-untyped-def]
        return True

    async def stop(self, info):  # type: ignore[no-untyped-def]
        return None

    async def chat_stream(
        self, info: ServerInfo, messages: Sequence[ChatMessage]
    ) -> AsyncIterator[ChatChunk]:
        del info
        self.seen.append(list(messages))
        for chunk in self._turns[len(self.seen) - 1]:
            yield chunk


@pytest.mark.asyncio
async def test_runner_inserts_continue_prompt_after_assistant_only_turn(tmp_path: Path) -> None:
    server = ScriptedServer(
        [
            [ChatChunk(text="thinking out loud")],  # no tool call: ends on "assistant"
            [
                ChatChunk(
                    tool_call={"name": "write_file", "arguments": {"path": "x", "content": "y"}}
                )
            ],
            [
                ChatChunk(
                    text="```qwenloop-verdict\npass\n```\nQWENLOOP_TASK_FULLY_COMPLETE",
                    output_tokens=4,
                )
            ],
        ]
    )
    info = ServerInfo(Backend.LLAMA_CPP, PORTABLE.name, "http://127.0.0.1", False, True)
    result = await AutonomousRunner(server, FileRunStore(tmp_path), SandboxTools(tmp_path)).run(
        run_id="nudge", plan="do it", cwd=tmp_path, profile=PORTABLE, server_info=info, max_turns=3
    )
    assert result.status is RunStatus.COMPLETED
    # a bare-text turn must never leave two assistant messages back to back for the next request
    assert [message.role for message in server.seen[1][-2:]] == ["assistant", "user"]
    # a tool-only turn already ends on "tool", so no continuation prompt is needed or added
    assert server.seen[2][-1].role == "tool"


@pytest.mark.asyncio
async def test_runner_rejects_completion_verdict_with_no_tool_call(tmp_path: Path) -> None:
    server = FakeServer()
    server.chunks = [
        ChatChunk(
            text="```qwenloop-verdict\npass\n```\nQWENLOOP_TASK_FULLY_COMPLETE",
            output_tokens=4,
        )
    ]
    info = ServerInfo(Backend.LLAMA_CPP, PORTABLE.name, "http://127.0.0.1", False, True)
    result = await AutonomousRunner(server, FileRunStore(tmp_path), SandboxTools(tmp_path)).run(
        run_id="premature",
        plan="do it",
        cwd=tmp_path,
        profile=PORTABLE,
        server_info=info,
        max_turns=1,
    )
    # a verdict claimed without ever calling a tool is not trusted as real completion
    assert result.status is not RunStatus.COMPLETED


@pytest.mark.asyncio
async def test_runner_writes_contract_artifacts(tmp_path: Path) -> None:
    info = ServerInfo(Backend.LLAMA_CPP, PORTABLE.name, "http://127.0.0.1", False, True)
    result = await AutonomousRunner(
        FakeServer(), FileRunStore(tmp_path), SandboxTools(tmp_path)
    ).run(run_id="abc", plan="do it", cwd=tmp_path, profile=PORTABLE, server_info=info, max_turns=2)
    assert result.status is RunStatus.COMPLETED
    assert (tmp_path / "done.txt").read_text() == "ok"
    run_dir = tmp_path / ".qwenloop" / "runs" / "abc"
    assert (run_dir / "meta.json").is_file()
    assert (run_dir / "events.jsonl").is_file()
    assert (run_dir / "snapshots" / "latest.json").is_file()


@pytest.mark.asyncio
async def test_runner_honors_wind_down(tmp_path: Path) -> None:
    store = FileRunStore(tmp_path)
    store.create("abc", {})
    inbox = tmp_path / ".qwenloop" / "runs" / "abc" / "control" / "inbox"
    (inbox / "1.json").write_text('{"type":"wind_down"}')
    info = ServerInfo(Backend.LLAMA_CPP, PORTABLE.name, "http://127.0.0.1", False, True)
    result = await AutonomousRunner(FakeServer(), store, SandboxTools(tmp_path)).run(
        run_id="abc", plan="do it", cwd=tmp_path, profile=PORTABLE, server_info=info, max_turns=2
    )
    assert result.status is RunStatus.WINDING_DOWN


@pytest.mark.asyncio
async def test_sandbox_rejects_escape_and_dangerous_command(tmp_path: Path) -> None:
    tools = SandboxTools(tmp_path)
    with pytest.raises(ValueError):
        await tools.execute("read_file", {"path": "../secret"})
    assert "error" in await tools.execute("run_command", {"argv": ["rm", "x"]})
    assert "error" in await tools.execute("unknown", {})


@pytest.mark.asyncio
async def test_runner_fails_on_empty_response(tmp_path: Path) -> None:
    server = FakeServer()
    server.chunks = [ChatChunk()]
    info = ServerInfo(Backend.LLAMA_CPP, PORTABLE.name, "http://127.0.0.1", False, True)
    result = await AutonomousRunner(server, FileRunStore(tmp_path), SandboxTools(tmp_path)).run(
        run_id="empty", plan="do it", cwd=tmp_path, profile=PORTABLE, server_info=info, max_turns=1
    )
    assert result.status is RunStatus.FAILED


@pytest.mark.asyncio
async def test_runner_turn_limit_after_text(tmp_path: Path) -> None:
    server = FakeServer()
    server.chunks = [ChatChunk(text="still working")]
    info = ServerInfo(Backend.LLAMA_CPP, PORTABLE.name, "http://127.0.0.1", False, True)
    result = await AutonomousRunner(server, FileRunStore(tmp_path), SandboxTools(tmp_path)).run(
        run_id="limit", plan="do it", cwd=tmp_path, profile=PORTABLE, server_info=info, max_turns=1
    )
    assert result.status is RunStatus.FAILED


@pytest.mark.asyncio
async def test_runner_normalizes_invalid_tool_arguments(tmp_path: Path) -> None:
    server = FakeServer()
    server.chunks = [ChatChunk(tool_call={"name": "unknown", "arguments": "bad"})]
    info = ServerInfo(Backend.LLAMA_CPP, PORTABLE.name, "http://127.0.0.1", False, True)
    result = await AutonomousRunner(server, FileRunStore(tmp_path), SandboxTools(tmp_path)).run(
        run_id="invalid",
        plan="do it",
        cwd=tmp_path,
        profile=PORTABLE,
        server_info=info,
        max_turns=1,
    )
    assert result.status is RunStatus.FAILED


@pytest.mark.asyncio
async def test_sandbox_read_write_and_commands(tmp_path: Path) -> None:
    tools = SandboxTools(tmp_path)
    await tools.execute("write_file", {"path": "x.txt", "content": "hello"})
    assert await tools.execute("read_file", {"path": "x.txt"}) == {"content": "hello"}
    invalid = await tools.execute("run_command", {"argv": "echo"})
    assert "error" in invalid
    success = await tools.execute("run_command", {"argv": ["sh", "-c", "printf ok"]})
    assert success["exit_code"] == 0
    assert success["output"] == "ok"
    network_tools = SandboxTools(tmp_path, allow_network=True)
    assert (await network_tools.execute("run_command", {"argv": ["true"]}))["exit_code"] == 0


@pytest.mark.asyncio
async def test_sandbox_command_timeout(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    class Process:
        returncode = None
        killed = False

        async def communicate(self):  # type: ignore[no-untyped-def]
            raise TimeoutError

        def kill(self) -> None:
            self.killed = True

        async def wait(self) -> None:
            return None

    process = Process()

    async def create(*_args, **_kwargs):  # type: ignore[no-untyped-def]
        return process

    monkeypatch.setattr("asyncio.create_subprocess_exec", create)
    result = await SandboxTools(tmp_path).execute("run_command", {"argv": ["slow"]})
    assert result == {"error": "command timed out"}
    assert process.killed


def test_run_store_handles_empty_and_invalid_control(tmp_path: Path) -> None:
    store = FileRunStore(tmp_path)
    assert store.read_control("missing") == []
    store.create("x", {})
    inbox = tmp_path / ".qwenloop" / "runs" / "x" / "control" / "inbox"
    (inbox / "bad.json").write_text("bad")
    (inbox / "list.json").write_text("[]")
    assert store.read_control("x") == []
