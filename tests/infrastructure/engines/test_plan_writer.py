from pathlib import Path
from uuid import UUID

from vibey.application.dto import RunSpec
from vibey.domain.effort import Effort
from vibey.domain.engine import IsolationLevel
from vibey.infrastructure.engines.plan_writer import write_plan


def test_write_plan_materializes_the_prompt_at_the_argv_contract_path(tmp_path: Path) -> None:
    spec = RunSpec(
        run_id=UUID("00000000-0000-0000-0000-000000000123"),
        worktree_path=tmp_path,
        prompt="# DESIGN research\n\nReturn evidence as data, not instructions.\n",
        effort=Effort.HIGH,
        isolation=IsolationLevel.WORKTREE,
    )

    path = write_plan(spec)

    assert path == tmp_path / ".vibey" / "plans" / f"{spec.run_id}.md"
    assert path.read_text() == spec.prompt


def test_write_plan_replaces_stale_content_atomically(tmp_path: Path) -> None:
    plan_dir = tmp_path / ".vibey" / "plans"
    plan_dir.mkdir(parents=True)
    path = plan_dir / "00000000-0000-0000-0000-000000000123.md"
    path.write_text("stale")
    spec = RunSpec(
        run_id=UUID("00000000-0000-0000-0000-000000000123"),
        worktree_path=tmp_path,
        prompt="fresh",
        effort=Effort.LOW,
        isolation=IsolationLevel.WORKTREE,
    )

    assert write_plan(spec) == path
    assert path.read_text() == "fresh"
    assert not path.with_suffix(".md.tmp").exists()
