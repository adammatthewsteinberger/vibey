# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Deterministic system harness: real FS/git/control + scripted agent, no Gemini."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.application.fakes import DONE_VERDICT, ScriptedTurn, available_signals
from tests.system.harness import build_system_harness

pytestmark = pytest.mark.system


async def test_scripted_run_completes_without_live_gemini(git_sandbox: Path) -> None:
    harness = build_system_harness(
        git_sandbox,
        turns=[ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT)],
        probes=[available_signals()],
    )
    result = await harness.runner.run(initial_prompt="do the plan", continue_prompt="continue")
    assert result.success is True
    assert result.reason == "all done"
    assert harness.gateway.sent_prompts == ["do the plan"]
    assert harness.gateway.closed is True
    assert (harness.run_dir.meta_path).is_file()
    meta = harness.run_dir.read_meta()
    assert meta.run_id == harness.run_id
    assert (git_sandbox / ".git").exists()
    assert (git_sandbox / ".agyloop" / "runs" / harness.run_id).is_dir()
    inbox = list(harness.run_dir.inbox.iterdir())
    assert inbox == []
