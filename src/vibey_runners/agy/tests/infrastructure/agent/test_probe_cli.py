# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""CLI capacity probe: one throwaway ``agy -p``, classified by the same ladder.

The point of this adapter is that ``--gateway cli`` keeps real capacity
detection instead of degrading to a no-op probe that reports Available forever.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from agyloop.domain.capacity import CreditsExhausted, WindowExhausted
from agyloop.domain.classify import classify
from agyloop.domain.errors import AgentConfigError
from agyloop.infrastructure.agent.cli_argv import AgyCliInvocation
from agyloop.infrastructure.agent.probe_cli import PROBE_PROMPT, AgyCliCapacityProbe


def _completed(
    returncode: int, stdout: str = "", stderr: str = ""
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=["agy"], returncode=returncode, stdout=stdout, stderr=stderr
    )


class _RecordingRunner:
    def __init__(self, result: subprocess.CompletedProcess[str]) -> None:
        self.result = result
        self.invocations: list[AgyCliInvocation] = []

    def __call__(
        self, invocation: AgyCliInvocation, *, cwd: Path
    ) -> subprocess.CompletedProcess[str]:
        self.invocations.append(invocation)
        return self.result


@pytest.mark.asyncio
async def test_probe_sends_the_cheap_prompt_without_a_conversation(tmp_path: Path) -> None:
    runner = _RecordingRunner(_completed(0, stdout="OK"))
    probe = AgyCliCapacityProbe(cwd=str(tmp_path), runner=runner)

    outcome = await probe.probe()

    assert outcome.output_text == "OK"
    assert outcome.session_id is None
    argv = runner.invocations[0].argv
    assert argv[:3] == ("agy", "-p", PROBE_PROMPT)
    # No --conversation: a probe must never resume or pollute the run's session.
    assert "--conversation" not in argv


@pytest.mark.asyncio
async def test_set_model_keeps_the_probe_on_the_runs_model(tmp_path: Path) -> None:
    runner = _RecordingRunner(_completed(0, stdout="OK"))
    probe = AgyCliCapacityProbe(cwd=str(tmp_path), runner=runner)

    probe.set_model("gemini-3-pro")
    await probe.probe()

    argv = runner.invocations[0].argv
    assert "--model" in argv and argv[argv.index("--model") + 1] == "gemini-3-pro"


@pytest.mark.asyncio
async def test_window_exhaustion_survives_the_cli_round_trip(tmp_path: Path) -> None:
    runner = _RecordingRunner(
        _completed(1, stderr="429 resource exhausted: quota exceeded for requests per minute")
    )
    probe = AgyCliCapacityProbe(cwd=str(tmp_path), runner=runner)

    outcome = await probe.probe()

    assert isinstance(classify(outcome.signals), WindowExhausted)


@pytest.mark.asyncio
async def test_credit_exhaustion_survives_the_cli_round_trip(tmp_path: Path) -> None:
    runner = _RecordingRunner(
        _completed(1, stderr="billing cap reached; purchase more credits to continue")
    )
    probe = AgyCliCapacityProbe(cwd=str(tmp_path), runner=runner)

    outcome = await probe.probe()

    assert isinstance(classify(outcome.signals), CreditsExhausted)


@pytest.mark.asyncio
async def test_an_unclassifiable_failure_fails_closed(tmp_path: Path) -> None:
    """A non-zero exit the ladder reads as Available is a broken invocation, not
    headroom. Reporting Available there would let the runner spend into a wall."""
    runner = _RecordingRunner(_completed(2, stderr="unknown flag: --nope"))
    probe = AgyCliCapacityProbe(cwd=str(tmp_path), runner=runner)

    with pytest.raises(AgentConfigError, match="unknown flag"):
        await probe.probe()


@pytest.mark.asyncio
async def test_missing_agy_cli_raises_config_error(tmp_path: Path) -> None:
    from unittest.mock import patch

    probe = AgyCliCapacityProbe(cwd=str(tmp_path))
    with (
        patch("shutil.which", return_value=None),
        pytest.raises(AgentConfigError, match="agy CLI not found on PATH"),
    ):
        await probe.probe()


@pytest.mark.asyncio
async def test_probe_cli_with_print_timeout(tmp_path: Path) -> None:
    runner = _RecordingRunner(_completed(0, stdout="OK"))
    probe = AgyCliCapacityProbe(cwd=str(tmp_path), print_timeout="15s", runner=runner)
    await probe.probe()
    argv = runner.invocations[0].argv
    assert "--print-timeout" in argv and argv[argv.index("--print-timeout") + 1] == "15s"
