# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
import shlex
from pathlib import Path
from uuid import UUID

import pytest

from vibey.application.dto import RunSpec
from vibey.domain.effort import Effort
from vibey.domain.engine import IsolationLevel
from vibey.infrastructure.engines.argv import build_argv
from vibey.infrastructure.engines.descriptors import ALL_DESCRIPTORS

GOLDEN_DIR = Path(__file__).parent / "golden"
RUN_ID = UUID("00000000-0000-0000-0000-000000000001")
WORKTREE = "/repo/.vibey/worktrees/c1-item-001"

ALL_EFFORTS = list(Effort)


def _spec(effort: Effort) -> RunSpec:
    return RunSpec(
        run_id=RUN_ID,
        worktree_path=Path(WORKTREE),
        prompt="implement the outbox relay",
        effort=effort,
        isolation=IsolationLevel.WORKTREE,
    )


@pytest.mark.parametrize("descriptor", ALL_DESCRIPTORS, ids=lambda d: d.engine_id.value)
@pytest.mark.parametrize("effort", ALL_EFFORTS, ids=lambda e: e.name)
def test_argv_matches_golden_file(descriptor, effort) -> None:  # type: ignore[no-untyped-def]
    argv = build_argv(descriptor, _spec(effort))
    golden_path = GOLDEN_DIR / f"{descriptor.engine_id.value}_{effort.name.lower()}.txt"

    expected = golden_path.read_text().strip()
    assert shlex.join(argv) == expected


def test_exactly_twenty_five_golden_files_exist() -> None:
    files = sorted(GOLDEN_DIR.glob("*.txt"))
    assert len(files) == 25


@pytest.mark.parametrize("descriptor", ALL_DESCRIPTORS, ids=lambda d: d.engine_id.value)
def test_new_run_uses_a_positional_plan_file_and_includes_run_id_flag(
    descriptor,
) -> None:  # type: ignore[no-untyped-def]
    argv = build_argv(descriptor, _spec(Effort.LOW))
    plan_index = 3 if descriptor.plan_flag is not None else 2
    if descriptor.plan_flag is not None:
        assert argv[2] == descriptor.plan_flag
    assert argv[plan_index] == f"{WORKTREE}/.vibey/plans/{RUN_ID}.md"
    assert "--run-id" in argv
    run_id_index = argv.index("--run-id")
    assert argv[run_id_index + 1] == str(RUN_ID)


@pytest.mark.parametrize("descriptor", ALL_DESCRIPTORS, ids=lambda d: d.engine_id.value)
def test_resume_verb_used_when_session_id_present(descriptor) -> None:  # type: ignore[no-untyped-def]
    spec = RunSpec(
        run_id=RUN_ID,
        worktree_path=Path(WORKTREE),
        prompt="continue",
        effort=Effort.LOW,
        isolation=IsolationLevel.WORKTREE,
        session_id="sess-abc123",
    )
    argv = build_argv(descriptor, spec)
    assert argv[1] == "resume"
    assert argv[2] == "sess-abc123"


@pytest.mark.parametrize("descriptor", ALL_DESCRIPTORS, ids=lambda d: d.engine_id.value)
def test_cwd_flag_presence_matches_descriptor_capability(descriptor) -> None:  # type: ignore[no-untyped-def]
    """build_argv() must never append --cwd for an engine whose real CLI
    doesn't accept it (codexloop `run` rejects it at argument parsing) --
    regression test for a bug that made LoopProcessAdapter unable to spawn
    codexloop at all, caught by a real subprocess-level conformance test."""
    argv = build_argv(descriptor, _spec(Effort.LOW))
    assert ("--cwd" in argv) == descriptor.supports_cwd_flag


@pytest.mark.parametrize("descriptor", ALL_DESCRIPTORS, ids=lambda d: d.engine_id.value)
def test_isolation_flags_included_for_container(descriptor) -> None:  # type: ignore[no-untyped-def]
    spec = RunSpec(
        run_id=RUN_ID,
        worktree_path=Path(WORKTREE),
        prompt="implement",
        effort=Effort.LOW,
        isolation=IsolationLevel.CONTAINER,
    )
    argv = build_argv(descriptor, spec)
    for flag in descriptor.isolation_flags[IsolationLevel.CONTAINER]:
        assert flag in argv


def test_plan_flag_engines_pass_the_plan_as_a_flag_not_a_positional() -> None:
    """cursorloop's `run` requires `--plan <path>`; the other three take a
    bare positional. Passing a positional to cursorloop killed every run at
    argument parsing (live finding: no run dir, no events, no snapshot)."""
    from vibey.infrastructure.engines.descriptors import CLAUDELOOP, CURSORLOOP

    spec = _spec(Effort.STANDARD)

    cursor_argv = build_argv(CURSORLOOP, spec)
    assert cursor_argv[1:3] == ("run", "--plan")
    assert cursor_argv[3].endswith(".md")

    claude_argv = build_argv(CLAUDELOOP, spec)
    assert claude_argv[1] == "run"
    assert claude_argv[2].endswith(".md")
    assert "--plan" not in claude_argv
