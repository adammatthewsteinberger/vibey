# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""ExecCapacityProbe: ephemeral read-only argv, classify outcomes, spawn failures."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from codexloop.application.dto import ProbeResult
from codexloop.application.ports import CapacityProbe
from codexloop.domain.capacity import Available, QuotaExhausted, TransientBackendError
from codexloop.domain.errors import CodexBinaryError
from codexloop.infrastructure.agent.probe import ExecCapacityProbe
from codexloop.infrastructure.agent.process import ProcessResult

JSONL = Path(__file__).resolve().parents[1] / "fixtures" / "jsonl"
CLEAN_THREAD_ID = "0199a213-81c0-7800-8aa1-bbab2a035a53"
QUOTA_THREAD_ID = "0199a213-81c0-7800-8aa1-bbab2a035a56"


def _result_from_fixture(name: str, *, exit_code: int = 0) -> ProcessResult:
    lines = (JSONL / f"{name}.jsonl").read_text(encoding="utf-8").splitlines()
    return ProcessResult(
        stdout_lines=lines,
        stderr_tail="",
        exit_code=exit_code,
        truncated_lines=0,
    )


class _ArgvSpy:
    def __init__(self, result: ProcessResult | BaseException) -> None:
        self.argvs: list[list[str]] = []
        self._result = result

    async def __call__(
        self,
        argv: Sequence[str],
        *,
        cwd: str | Path,
        env: Mapping[str, str],
        timeout: float,
        max_line_bytes: int,
    ) -> ProcessResult:
        del cwd, env, timeout, max_line_bytes
        self.argvs.append(list(argv))
        if isinstance(self._result, BaseException):
            raise self._result
        return self._result


def _probe(tmp_path: Path, *, run: _ArgvSpy) -> ExecCapacityProbe:
    return ExecCapacityProbe(cwd=tmp_path, env={}, run_codex=run)


async def test_probe_argv_is_ephemeral_read_only_and_never_resumes(tmp_path: Path) -> None:
    spy = _ArgvSpy(_result_from_fixture("clean_completion"))
    probe = _probe(tmp_path, run=spy)

    result = await probe.probe()

    assert isinstance(probe, CapacityProbe)
    assert isinstance(result, ProbeResult)
    assert len(spy.argvs) == 1
    argv = spy.argvs[0]
    assert "--ephemeral" in argv
    assert 'sandbox_mode="read-only"' in argv
    assert "resume" not in argv
    assert "--last" not in argv
    assert CLEAN_THREAD_ID not in argv


async def test_second_probe_still_does_not_write_to_the_run_thread(tmp_path: Path) -> None:
    spy = _ArgvSpy(_result_from_fixture("clean_completion"))
    probe = _probe(tmp_path, run=spy)

    await probe.probe()
    await probe.probe()

    assert len(spy.argvs) == 2
    for argv in spy.argvs:
        assert "--ephemeral" in argv
        assert "resume" not in argv
        assert "--last" not in argv
        assert CLEAN_THREAD_ID not in argv


async def test_successful_probe_yields_available(tmp_path: Path) -> None:
    spy = _ArgvSpy(_result_from_fixture("clean_completion"))
    result = await _probe(tmp_path, run=spy).probe()

    assert result.outcome == Available()


async def test_rejected_probe_yields_classified_state(tmp_path: Path) -> None:
    spy = _ArgvSpy(_result_from_fixture("turn_failed_429_quota", exit_code=2))
    result = await _probe(tmp_path, run=spy).probe()

    assert result.outcome == QuotaExhausted(reason="insufficient_quota")
    assert QUOTA_THREAD_ID not in spy.argvs[0]
    assert "resume" not in spy.argvs[0]


async def test_spawn_failure_yields_transient_backend_error_rather_than_raising(
    tmp_path: Path,
) -> None:
    spy = _ArgvSpy(FileNotFoundError("codex"))
    result = await _probe(tmp_path, run=spy).probe()

    assert isinstance(result.outcome, TransientBackendError)
    assert spy.argvs  # argv was built before spawn failed


async def test_codex_binary_error_yields_transient_backend_error_rather_than_raising(
    tmp_path: Path,
) -> None:
    spy = _ArgvSpy(CodexBinaryError("failed to spawn"))
    result = await _probe(tmp_path, run=spy).probe()

    assert isinstance(result.outcome, TransientBackendError)
