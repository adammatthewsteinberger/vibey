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


def test_exactly_twenty_golden_files_exist() -> None:
    files = sorted(GOLDEN_DIR.glob("*.txt"))
    assert len(files) == 20


@pytest.mark.parametrize("descriptor", ALL_DESCRIPTORS, ids=lambda d: d.engine_id.value)
def test_new_run_uses_a_positional_plan_file_and_includes_run_id_flag(
    descriptor,
) -> None:  # type: ignore[no-untyped-def]
    argv = build_argv(descriptor, _spec(Effort.LOW))
    assert argv[2] == f"{WORKTREE}/.vibey/plans/{RUN_ID}.md"
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
