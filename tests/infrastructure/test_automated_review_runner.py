# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from vibey.application.build_verify_handler import GateResult, GateRunner
from vibey.application.dto import ProjectRecord
from vibey.domain.phase import Phase
from vibey.domain.review import Ambiguity, Severity
from vibey.infrastructure.build.automated_review_runner import SubprocessAutomatedReviewRunner

NOW = datetime(2026, 8, 15, tzinfo=UTC)


class FakeGateRunner(GateRunner):
    def __init__(self, outcomes: dict[tuple[str, ...], GateResult] | None = None) -> None:
        self.outcomes = outcomes or {}

    async def run(self, argv: tuple[str, ...], *, cwd: Path) -> GateResult:
        return self.outcomes.get(argv, GateResult(0, "ok", ""))


class FakeProjectRepo:
    def __init__(self, project: ProjectRecord | None = None) -> None:
        self.project = project

    async def get(self, project_id: object) -> ProjectRecord | None:
        return self.project


async def test_subprocess_automated_review_runner_clean(tmp_path: Path) -> None:
    proj = ProjectRecord(
        project_id=uuid4(),
        name="p1",
        repo_path=tmp_path,
        phase=Phase.REVIEW,
        cycle=1,
        max_cycles=5,
        config={},
        created_at=NOW,
        updated_at=NOW,
    )
    runner = SubprocessAutomatedReviewRunner(
        projects=FakeProjectRepo(proj),
        gates=FakeGateRunner(),
    )
    findings = await runner.run_automated_reviews(proj.project_id, 1)
    assert len(findings) == 0


async def test_subprocess_automated_review_runner_detects_security_and_code_findings(
    tmp_path: Path,
) -> None:
    proj = ProjectRecord(
        project_id=uuid4(),
        name="p1",
        repo_path=tmp_path,
        phase=Phase.REVIEW,
        cycle=1,
        max_cycles=5,
        config={},
        created_at=NOW,
        updated_at=NOW,
    )
    sec_cmd = ("bandit", "-q", "-r", "src")
    code_cmd = ("ruff", "check", ".")
    gates = FakeGateRunner(
        outcomes={
            sec_cmd: GateResult(1, "", "B101: assert used"),
            code_cmd: GateResult(1, "E501: line too long", ""),
        }
    )
    runner = SubprocessAutomatedReviewRunner(
        projects=FakeProjectRepo(proj),
        gates=gates,
        security_commands=(sec_cmd,),
        code_review_commands=(code_cmd,),
    )
    findings = await runner.run_automated_reviews(proj.project_id, 1)
    assert len(findings) == 2

    sec = next(f for f in findings if f.category == "security")
    assert sec.severity == Severity.HIGH
    assert sec.ambiguity == Ambiguity.CLEAR
    assert "B101" in sec.text

    code = next(f for f in findings if f.category == "code_review")
    assert code.severity == Severity.MEDIUM
    assert code.ambiguity == Ambiguity.CLEAR
    assert "E501" in code.text


async def test_subprocess_automated_review_runner_unknown_project() -> None:
    runner = SubprocessAutomatedReviewRunner(
        projects=FakeProjectRepo(None),
        gates=FakeGateRunner(),
    )
    with pytest.raises(LookupError):
        await runner.run_automated_reviews(uuid4(), 1)

    runner_invalid = SubprocessAutomatedReviewRunner(
        projects=object(),
        gates=FakeGateRunner(),
    )
    with pytest.raises(LookupError):
        await runner_invalid.run_automated_reviews(uuid4(), 1)


def test_default_code_review_command_excludes_vibey_machinery() -> None:
    """`ruff check .` at the repo root must never review .vibey worktrees
    or engine state dirs -- a stale worktree's dead code raised a real
    finding live and looped REVIEW back into BUILD."""
    from vibey.infrastructure.build.automated_review_runner import _DEFAULT_CODE_REVIEW

    (command,) = _DEFAULT_CODE_REVIEW
    assert command[:3] == ("ruff", "check", ".")
    for name in (".vibey", ".claudeloop", ".codexloop", ".cursorloop", ".agyloop"):
        index = command.index(name)
        assert command[index - 1] == "--exclude"
