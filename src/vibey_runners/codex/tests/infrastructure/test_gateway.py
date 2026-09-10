# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""CodexExecGateway: exec then resume-by-id, failed turns, idempotent close."""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

import pytest

from codexloop.application.dto import TurnOutcome
from codexloop.application.ports import AgentGateway, PermissionMode
from codexloop.domain.approval import ApprovalPolicy, SandboxMode
from codexloop.domain.model_profile import Effort, ModelEffortProfile
from codexloop.infrastructure.agent.events import JsonlParser, ThreadStarted
from codexloop.infrastructure.agent.gateway import CodexExecGateway
from codexloop.infrastructure.agent.process import ProcessResult, run_codex

JSONL = Path(__file__).resolve().parents[1] / "fixtures" / "jsonl"
CLEAN_THREAD_ID = "0199a213-81c0-7800-8aa1-bbab2a035a53"
QUOTA_THREAD_ID = "0199a213-81c0-7800-8aa1-bbab2a035a56"


def _env() -> dict[str, str]:
    return os.environ.copy()


class _ArgvSpy:
    def __init__(self) -> None:
        self.argvs: list[list[str]] = []
        self.cwds: list[str] = []

    async def __call__(
        self,
        argv: Sequence[str],
        *,
        cwd: str | Path,
        env: Mapping[str, str],
        timeout: float,
        max_line_bytes: int,
    ) -> ProcessResult:
        self.argvs.append(list(argv))
        self.cwds.append(os.fspath(cwd))
        return await run_codex(
            argv, cwd=cwd, env=env, timeout=timeout, max_line_bytes=max_line_bytes
        )


def _gateway(
    tmp_path: Path,
    *,
    run: Callable[..., object] | None = None,
) -> CodexExecGateway:
    return CodexExecGateway(
        cwd=tmp_path,
        env=_env(),
        run_codex=run,
        timeout=15.0,
        max_line_bytes=65_536,
    )


async def test_first_turn_is_exec_second_is_resume_by_captured_id(
    fake_codex_on_path: Path,
    configure_fake_codex: Callable[..., None],
    tmp_path: Path,
) -> None:
    configure_fake_codex(script=JSONL / "clean_completion.jsonl", mode="stream")
    spy = _ArgvSpy()
    gateway = _gateway(tmp_path, run=spy)

    first = await gateway.send_turn("first prompt")
    second = await gateway.send_turn("second prompt")

    assert isinstance(gateway, AgentGateway)
    assert first.signals is not None
    assert first.signals.completed is True
    assert first.exit_code == 0
    assert second.signals is not None
    assert second.exit_code == 0

    assert len(spy.argvs) == 2
    assert spy.argvs[0][:3] == ["codex", "exec", "--json"]
    assert "resume" not in spy.argvs[0]
    assert "--last" not in spy.argvs[0]
    assert spy.argvs[0][-1] == "first prompt"

    assert spy.argvs[1][:4] == ["codex", "exec", "resume", CLEAN_THREAD_ID]
    assert "--last" not in spy.argvs[1]
    assert spy.argvs[1][-1] == "second prompt"

    parser = JsonlParser()
    started = parser.parse_line(
        (JSONL / "clean_completion.jsonl").read_text(encoding="utf-8").splitlines()[0]
    )
    assert isinstance(started, ThreadStarted)
    assert started.thread_id == CLEAN_THREAD_ID
    assert spy.argvs[1][3] == started.thread_id


async def test_close_is_idempotent(
    fake_codex_on_path: Path,
    tmp_path: Path,
) -> None:
    gateway = _gateway(tmp_path)
    await gateway.close()
    await gateway.close()


async def test_failed_turn_returns_turn_outcome_rather_than_raising(
    fake_codex_on_path: Path,
    configure_fake_codex: Callable[..., None],
    tmp_path: Path,
) -> None:
    configure_fake_codex(script=JSONL / "turn_failed_429_quota.jsonl", mode="exit_nonzero")
    spy = _ArgvSpy()
    gateway = _gateway(tmp_path, run=spy)

    outcome = await gateway.send_turn("do the thing")

    assert isinstance(outcome, TurnOutcome)
    assert outcome.signals is not None
    assert outcome.signals.failed is True
    assert outcome.signals.error_code == "insufficient_quota"
    assert outcome.exit_code == 2
    assert spy.argvs[0][:3] == ["codex", "exec", "--json"]
    second = await gateway.send_turn("retry")
    assert isinstance(second, TurnOutcome)
    assert spy.argvs[1][:4] == ["codex", "exec", "resume", QUOTA_THREAD_ID]
    assert "--last" not in spy.argvs[1]


async def test_set_profile_appears_on_next_exec_argv(
    fake_codex_on_path: Path,
    configure_fake_codex: Callable[..., None],
    tmp_path: Path,
) -> None:
    configure_fake_codex(script=JSONL / "clean_completion.jsonl", mode="stream")
    spy = _ArgvSpy()
    gateway = _gateway(tmp_path, run=spy)
    await gateway.set_profile(ModelEffortProfile.high("o3"))
    await gateway.send_turn("go")
    argv = spy.argvs[0]
    assert argv[argv.index("--model") + 1] == "o3"
    assert 'model_reasoning_effort="high"' in argv
    assert gateway._opts.model == "o3"
    assert gateway._opts.effort is Effort.HIGH


@pytest.mark.parametrize(
    ("mode", "approval", "sandbox"),
    [
        (PermissionMode.AUTONOMOUS, ApprovalPolicy.NEVER, SandboxMode.WORKSPACE_WRITE),
        (PermissionMode.READ_ONLY, ApprovalPolicy.NEVER, SandboxMode.READ_ONLY),
        (PermissionMode.FULL_ACCESS, ApprovalPolicy.NEVER, SandboxMode.DANGER_FULL_ACCESS),
    ],
)
async def test_set_permission_mode_maps_to_approval_and_sandbox(
    fake_codex_on_path: Path,
    configure_fake_codex: Callable[..., None],
    tmp_path: Path,
    mode: PermissionMode,
    approval: ApprovalPolicy,
    sandbox: SandboxMode,
) -> None:
    configure_fake_codex(script=JSONL / "clean_completion.jsonl", mode="stream")
    spy = _ArgvSpy()
    gateway = _gateway(tmp_path, run=spy)
    await gateway.set_permission_mode(mode)
    await gateway.send_turn("go")
    argv = spy.argvs[0]
    assert f'approval_policy="{approval.value}"' in argv
    assert f'sandbox_mode="{sandbox.value}"' in argv


async def test_set_cwd_is_passed_to_run_codex(
    fake_codex_on_path: Path,
    configure_fake_codex: Callable[..., None],
    tmp_path: Path,
) -> None:
    configure_fake_codex(script=JSONL / "clean_completion.jsonl", mode="stream")
    nested = tmp_path / "nested"
    nested.mkdir()
    spy = _ArgvSpy()
    gateway = _gateway(tmp_path, run=spy)
    await gateway.set_cwd(str(nested))
    await gateway.send_turn("go")
    assert spy.cwds == [str(nested)]


async def test_set_session_resources_add_dirs_and_ignores_invalid(
    fake_codex_on_path: Path,
    configure_fake_codex: Callable[..., None],
    tmp_path: Path,
) -> None:
    configure_fake_codex(script=JSONL / "clean_completion.jsonl", mode="stream")
    spy = _ArgvSpy()
    gateway = _gateway(tmp_path, run=spy)
    await gateway.set_session_resources({"add_dirs": 1})
    await gateway.set_session_resources({"add_dirs": ["ok", 2]})
    await gateway.set_session_resources({"other": ["x"]})
    assert gateway._opts.add_dirs == ()
    await gateway.set_session_resources({"add_dirs": ("/extra-a", "/extra-b")})
    await gateway.set_session_resources(
        {"approval_policy": "on-request", "sandbox_mode": "read-only"}
    )
    assert gateway._opts.approval.value == "on-request"
    assert gateway._opts.sandbox.value == "read-only"
    await gateway.send_turn("go")
    argv = spy.argvs[0]
    assert argv.count("--add-dir") == 2
    assert "/extra-a" in argv
    assert "/extra-b" in argv
    assert 'approval_policy="on-request"' in argv
    assert 'sandbox_mode="read-only"' in argv


async def test_close_after_set_is_idempotent_and_keeps_settings(
    fake_codex_on_path: Path,
    configure_fake_codex: Callable[..., None],
    tmp_path: Path,
) -> None:
    configure_fake_codex(script=JSONL / "clean_completion.jsonl", mode="stream")
    spy = _ArgvSpy()
    gateway = _gateway(tmp_path, run=spy)
    await gateway.set_profile(ModelEffortProfile.low("gpt-5"))
    await gateway.set_permission_mode(PermissionMode.READ_ONLY)
    await gateway.close()
    await gateway.close()
    await gateway.send_turn("still works")
    argv = spy.argvs[0]
    assert argv[argv.index("--model") + 1] == "gpt-5"
    assert 'sandbox_mode="read-only"' in argv


def test_resolve_tool_approval_returns_allow_flag(tmp_path: Path) -> None:
    gateway = _gateway(tmp_path)
    assert gateway.resolve_tool_approval("req-1", allow=True, reason="ok") is True
    assert gateway.resolve_tool_approval("req-2", allow=False) is False


async def test_thread_started_without_id_does_not_record_and_stays_on_exec(
    fake_codex_on_path: Path,
    tmp_path: Path,
) -> None:
    async def _run(
        argv: Sequence[str],
        *,
        cwd: str | Path,
        env: Mapping[str, str],
        timeout: float,
        max_line_bytes: int,
    ) -> ProcessResult:
        del argv, cwd, env, timeout, max_line_bytes
        return ProcessResult(
            stdout_lines=[
                '{"type":"turn.started"}',
                '{"type":"thread.started","thread_id":""}',
                '{"type":"thread.started"}',
            ],
            stderr_tail="",
            exit_code=0,
            truncated_lines=0,
        )

    gateway = _gateway(tmp_path, run=_run)
    first = await gateway.send_turn("one")
    second = await gateway.send_turn("two")
    assert first.exit_code == 0
    assert second.exit_code == 0
    assert gateway._thread_id is None


async def test_send_turn_wires_output_schema_and_loads_structured_output(
    fake_codex_on_path: Path,
    configure_fake_codex: Callable[..., None],
    tmp_path: Path,
) -> None:
    configure_fake_codex(script=JSONL / "clean_completion.jsonl", mode="stream")
    spy = _ArgvSpy()
    gateway = _gateway(tmp_path, run=spy)
    last_message = tmp_path / ".codexloop" / "last-message.json"

    async def _run_and_write(
        argv: Sequence[str],
        *,
        cwd: str | Path,
        env: Mapping[str, str],
        timeout: float,
        max_line_bytes: int,
    ) -> ProcessResult:
        last_message.parent.mkdir(parents=True, exist_ok=True)
        last_message.write_text(
            '{"complete": true, "remaining_work": []}\n',
            encoding="utf-8",
        )
        return await spy(argv, cwd=cwd, env=env, timeout=timeout, max_line_bytes=max_line_bytes)

    gateway = CodexExecGateway(
        cwd=tmp_path,
        env=_env(),
        run_codex=_run_and_write,
        timeout=15.0,
        max_line_bytes=65_536,
    )
    outcome = await gateway.send_turn("finish")
    argv = spy.argvs[0]
    assert "--output-schema" in argv
    assert "--output-last-message" in argv
    assert outcome.signals is not None
    assert outcome.signals.structured_output == {
        "complete": True,
        "remaining_work": [],
    }


def test_read_structured_handles_missing_empty_and_non_json(tmp_path: Path) -> None:
    from unittest.mock import MagicMock

    from codexloop.infrastructure.agent.gateway import _read_structured

    missing = tmp_path / "nope.json"
    assert _read_structured(missing) is None

    empty = tmp_path / "empty.json"
    empty.write_text("   \n", encoding="utf-8")
    assert _read_structured(empty) is None

    plain = tmp_path / "plain.json"
    plain.write_text("not-json\n", encoding="utf-8")
    assert _read_structured(plain) == "not-json"

    boom = MagicMock()
    boom.is_file.return_value = True
    boom.read_text.side_effect = OSError("boom")
    assert _read_structured(boom) is None


async def test_send_turn_unlinks_stale_last_message(
    fake_codex_on_path: Path,
    configure_fake_codex: Callable[..., None],
    tmp_path: Path,
) -> None:
    configure_fake_codex(script=JSONL / "clean_completion.jsonl", mode="stream")
    control = tmp_path / ".codexloop"
    control.mkdir(parents=True)
    stale = control / "last-message.json"
    stale.write_text('{"complete": false}\n', encoding="utf-8")
    gateway = _gateway(tmp_path)
    await gateway.send_turn("go")
    # Fresh turn clears then rewrites only if the CLI produced output; after a clean
    # fake stream with no last-message write, the stale file must be gone.
    assert not stale.exists() or stale.read_text(encoding="utf-8") != '{"complete": false}\n'


class _EventSinkSpy:
    """Test spy that records emitted events."""

    def __init__(self) -> None:
        self.events: list[Mapping[str, object]] = []

    def emit(self, event: Mapping[str, object]) -> None:
        self.events.append(dict(event))


async def test_send_turn_emits_events_to_sink_when_provided(
    fake_codex_on_path: Path,
    configure_fake_codex: Callable[..., None],
    tmp_path: Path,
) -> None:
    """Regression test: events parsed from codex stdout must be persisted to the sink."""
    configure_fake_codex(script=JSONL / "tool_heavy.jsonl", mode="stream")
    sink = _EventSinkSpy()
    gateway = CodexExecGateway(
        cwd=tmp_path,
        env=_env(),
        timeout=15.0,
        max_line_bytes=65_536,
        event_sink=sink,
    )

    await gateway.send_turn("run tools")

    # tool_heavy has: ThreadStarted, TurnStarted, 4 ItemStarted, 4 ItemCompleted, TurnCompleted
    assert len(sink.events) >= 10  # at least all the structured events
    types = [e.get("type") for e in sink.events]
    assert "thread.started" in types
    assert "turn.started" in types
    assert "turn.completed" in types
    assert types.count("item.started") >= 3
    assert types.count("item.completed") >= 3

    # Verify thread.started carries thread_id
    thread_started_events = [e for e in sink.events if e.get("type") == "thread.started"]
    assert len(thread_started_events) == 1
    assert thread_started_events[0].get("thread_id") is not None

    # Verify turn.completed carries usage
    turn_completed_events = [e for e in sink.events if e.get("type") == "turn.completed"]
    assert len(turn_completed_events) == 1
    assert turn_completed_events[0].get("usage") is not None


async def test_send_turn_skips_unparseable_lines_when_emitting(
    tmp_path: Path,
) -> None:
    """A blank/malformed stdout line parses to None and must be skipped
    when forwarding to the sink, not emitted or raised on."""

    async def _run(
        argv: Sequence[str],
        *,
        cwd: str | Path,
        env: Mapping[str, str],
        timeout: float,
        max_line_bytes: int,
    ) -> ProcessResult:
        del argv, cwd, env, timeout, max_line_bytes
        return ProcessResult(
            stdout_lines=[
                "",
                '{"type":"turn.started"}',
            ],
            stderr_tail="",
            exit_code=0,
            truncated_lines=0,
        )

    sink = _EventSinkSpy()
    gateway = CodexExecGateway(
        cwd=tmp_path,
        env=_env(),
        run_codex=_run,
        timeout=15.0,
        max_line_bytes=65_536,
        event_sink=sink,
    )

    await gateway.send_turn("one")

    assert [e.get("type") for e in sink.events] == ["turn.started"]


async def test_send_turn_works_without_event_sink(
    fake_codex_on_path: Path,
    configure_fake_codex: Callable[..., None],
    tmp_path: Path,
) -> None:
    """Event sink is optional; send_turn must not fail when None."""
    configure_fake_codex(script=JSONL / "clean_completion.jsonl", mode="stream")
    gateway = CodexExecGateway(
        cwd=tmp_path,
        env=_env(),
        timeout=15.0,
        max_line_bytes=65_536,
        event_sink=None,
    )

    outcome = await gateway.send_turn("test")

    assert outcome.exit_code == 0
    assert outcome.signals is not None
    assert outcome.signals.completed is True
