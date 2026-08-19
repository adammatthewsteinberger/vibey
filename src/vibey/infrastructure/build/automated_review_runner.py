"""Infrastructure runner for automated security and code review checks."""

from collections.abc import Sequence
from pathlib import Path
from uuid import UUID

from vibey.application.build_verify_handler import GateRunner
from vibey.application.interfaces import (
    ProjectStore,
)
from vibey.application.review_demo_handler import AutomatedFinding
from vibey.domain.review import Ambiguity, Severity

# vibey's own machinery inside the project repo -- worktrees under .vibey/
# and the engines' state dirs. Reviewing them reviews dead attempt branches
# and run transcripts, not the product: caught live when a stale cycle's
# worktree raised a lint finding against code that no longer existed,
# looping REVIEW back into BUILD.
_MACHINERY_DIRS = (".vibey", ".claudeloop", ".codexloop", ".cursorloop", ".agyloop")

_DEFAULT_CODE_REVIEW: tuple[tuple[str, ...], ...] = (
    ("ruff", "check", ".")
    + tuple(part for name in _MACHINERY_DIRS for part in ("--exclude", name)),
)


class SubprocessAutomatedReviewRunner:
    def __init__(
        self,
        *,
        projects: ProjectStore | object,
        gates: GateRunner,
        security_commands: Sequence[tuple[str, ...]] = (("bandit", "-q", "-r", "src"),),
        code_review_commands: Sequence[tuple[str, ...]] = _DEFAULT_CODE_REVIEW,
    ) -> None:
        self._projects = projects
        self._gates = gates
        self._security_commands = tuple(security_commands)
        self._code_review_commands = tuple(code_review_commands)

    async def _get_repo_path(self, project_id: UUID) -> Path:
        if hasattr(self._projects, "get"):
            proj = await self._projects.get(project_id)
            if proj is None:
                raise LookupError(f"unknown project {project_id}")
            return Path(proj.repo_path)
        raise LookupError(f"cannot resolve repo path for {project_id}")

    async def run_automated_reviews(
        self, project_id: UUID, cycle: int
    ) -> tuple[AutomatedFinding, ...]:
        repo_path = await self._get_repo_path(project_id)
        findings: list[AutomatedFinding] = []

        for cmd in self._security_commands:
            result = await self._gates.run(cmd, cwd=repo_path)
            if result.returncode != 0:
                detail = (result.stderr or result.stdout).strip()
                findings.append(
                    AutomatedFinding(
                        category="security",
                        text=f"Security check failed ({' '.join(cmd)}): {detail}",
                        severity=Severity.HIGH,
                        ambiguity=Ambiguity.CLEAR,
                    )
                )

        for cmd in self._code_review_commands:
            result = await self._gates.run(cmd, cwd=repo_path)
            if result.returncode != 0:
                detail = (result.stderr or result.stdout).strip()
                findings.append(
                    AutomatedFinding(
                        category="code_review",
                        text=f"Code review check failed ({' '.join(cmd)}): {detail}",
                        severity=Severity.MEDIUM,
                        ambiguity=Ambiguity.CLEAR,
                    )
                )

        return tuple(findings)
