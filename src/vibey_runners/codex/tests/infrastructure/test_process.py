# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Supervised Codex subprocess: concurrent pumps, line ceiling, timeout, orphans, stdin."""

from __future__ import annotations

import contextlib
import os
import signal
from collections.abc import Callable, Mapping
from pathlib import Path

import anyio
import pytest

from codexloop.domain.errors import CodexBinaryError
from codexloop.infrastructure.agent.process import STDERR_TAIL_BYTES, ProcessResult, run_codex

_ARGV = ["codex", "exec", "--json", "--", "probe"]


def _env() -> dict[str, str]:
    return os.environ.copy()


async def _run(
    tmp_path: Path,
    *,
    timeout: float = 15.0,
    max_line_bytes: int = 65_536,
    env: Mapping[str, str] | None = None,
) -> ProcessResult:
    return await run_codex(
        _ARGV,
        cwd=tmp_path,
        env=_env() if env is None else env,
        timeout=timeout,
        max_line_bytes=max_line_bytes,
    )


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _read_orphan_pair(marker: Path) -> tuple[int, int] | None:
    if not marker.is_file():
        return None
    try:
        text = marker.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    parts = text.split()
    if len(parts) != 2:
        return None
    try:
        return int(parts[0]), int(parts[1])
    except ValueError:
        return None


async def test_empty_argv_raises_named_error(tmp_path: Path) -> None:
    with pytest.raises(CodexBinaryError, match="non-empty"):
        await run_codex([], cwd=tmp_path, env=_env(), timeout=1.0, max_line_bytes=64)


# --- Concurrency --------------------------------------------------------------


async def test_concurrent_stdout_and_stderr_do_not_deadlock(
    fake_codex_on_path: Path,
    configure_fake_codex: Callable[..., None],
    tmp_path: Path,
) -> None:
    configure_fake_codex(mode="both_streams")
    with anyio.fail_after(10):
        result = await _run(tmp_path, timeout=10.0)
    assert result.exit_code == 0
    assert len(result.stdout_lines) >= 1000
    assert all(line.startswith("O") for line in result.stdout_lines)
    assert "E" in result.stderr_tail
    assert len(result.stderr_tail.encode("utf-8")) <= STDERR_TAIL_BYTES


# --- Line ceiling -------------------------------------------------------------


async def test_oversized_line_is_truncated_counted_and_does_not_raise(
    fake_codex_on_path: Path,
    configure_fake_codex: Callable[..., None],
    tmp_path: Path,
) -> None:
    configure_fake_codex(mode="huge_line")
    max_line_bytes = 4096
    result = await _run(tmp_path, max_line_bytes=max_line_bytes)
    assert result.exit_code == 0
    assert result.truncated_lines >= 1
    assert result.stdout_lines
    assert all(len(line.encode("utf-8")) <= max_line_bytes for line in result.stdout_lines)
    assert len(result.stdout_lines[0].encode("utf-8")) == max_line_bytes
    assert not any(len(line.encode("utf-8")) > max_line_bytes for line in result.stdout_lines)


# --- Timeout ------------------------------------------------------------------


async def test_hang_times_out_with_named_timeout(
    fake_codex_on_path: Path,
    configure_fake_codex: Callable[..., None],
    tmp_path: Path,
) -> None:
    configure_fake_codex(mode="hang")
    with pytest.raises(CodexBinaryError, match=r"timed out after 0\.2"):
        await _run(tmp_path, timeout=0.2)


def test_read_orphan_pair_returns_none_for_missing_or_bad_marker(tmp_path: Path) -> None:
    assert _read_orphan_pair(tmp_path / "missing.pids") is None
    bad = tmp_path / "bad.pids"
    bad.write_text("not-pids\n", encoding="utf-8")
    assert _read_orphan_pair(bad) is None


# --- Orphan / cancellation ----------------------------------------------------


async def test_cancel_kills_child_and_grandchild(
    fake_codex_on_path: Path,
    configure_fake_codex: Callable[..., None],
    tmp_path: Path,
) -> None:
    marker = tmp_path / "orphan.pids"
    configure_fake_codex(mode="orphan_child")
    env = _env()
    env["FAKE_CODEX_ORPHAN_MARKER"] = str(marker)
    parent_pid: int | None = None
    grandchild_pid: int | None = None

    async def _invoke() -> None:
        await _run(tmp_path, timeout=30.0, env=env)

    try:
        async with anyio.create_task_group() as tg:
            tg.start_soon(_invoke)
            deadline = anyio.current_time() + 10.0
            while anyio.current_time() < deadline:
                found = _read_orphan_pair(marker)
                if found is not None:
                    parent_pid, grandchild_pid = found
                    break
                await anyio.sleep(0.05)
            else:
                pytest.fail("orphan pid marker never appeared")
            tg.cancel_scope.cancel()
    finally:
        assert parent_pid is not None
        assert grandchild_pid is not None
        deadline = anyio.current_time() + 5.0
        while anyio.current_time() < deadline:
            if not _pid_alive(parent_pid) and not _pid_alive(grandchild_pid):
                break
            await anyio.sleep(0.05)
        else:
            survivors = {
                "parent": parent_pid if _pid_alive(parent_pid) else None,
                "grandchild": grandchild_pid if _pid_alive(grandchild_pid) else None,
            }
            for pid in (parent_pid, grandchild_pid):
                with contextlib.suppress(ProcessLookupError, PermissionError):
                    os.kill(pid, signal.SIGKILL)
            pytest.fail(f"process group members survived cancellation: {survivors}")


# --- Stdin --------------------------------------------------------------------


async def test_child_stdin_is_not_a_tty_and_reads_eof(
    fake_codex_on_path: Path,
    configure_fake_codex: Callable[..., None],
    tmp_path: Path,
) -> None:
    configure_fake_codex(mode="stdin_probe")
    result = await _run(tmp_path)
    text = "\n".join(result.stdout_lines) + "\n" + result.stderr_tail
    assert "tty=False" in text
    assert "eof=True" in text
    assert result.exit_code == 0
