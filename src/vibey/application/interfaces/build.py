# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Phase 2 collaborators: worktrees, provisioning, budget, gates, integration."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable
from uuid import UUID

from vibey.domain.budget import BudgetLedger
from vibey.domain.plan import WorkItem
from vibey.domain.provision import ProvisionSpec
from vibey.domain.spec import DesignSpec


@dataclass(frozen=True, slots=True)
class MergeOutcome:
    ok: bool
    detail: str


@dataclass(frozen=True, slots=True)
class GateResult:
    """A verification gate's raw subprocess outcome.

    Distinct from `domain.handoff.GateResult`, which is the no-loss gate's
    verdict -- same word, unrelated concepts.
    """

    returncode: int
    stdout: str
    stderr: str


@runtime_checkable
class BudgetSource(Protocol):
    async def current(self, project_id: UUID, cycle: int) -> BudgetLedger: ...


@dataclass(frozen=True, slots=True)
class SkillsContextResult:
    """A context-packet attempt, with raw task text deliberately absent."""

    mode: str
    status: str
    markdown: str
    provenance: Mapping[str, object]

    @property
    def should_inject(self) -> bool:
        return self.mode == "inject" and self.status == "ok" and bool(self.markdown)


@runtime_checkable
class SkillsContextCompiler(Protocol):
    async def compile(self, *, job: object, worktree_path: Path) -> SkillsContextResult: ...


@runtime_checkable
class BuildProvisioner(Protocol):
    async def provision(self, worktree_path: Path, spec: ProvisionSpec) -> tuple[Path, ...]: ...


@runtime_checkable
class BuildWorktrees(Protocol):
    async def create(self, item_id: str, *, base_ref: str = "HEAD") -> Path: ...


@runtime_checkable
class GateRunner(Protocol):
    async def run(self, argv: tuple[str, ...], *, cwd: Path) -> GateResult: ...


@runtime_checkable
class IntegrationBranch(Protocol):
    async def ensure(self) -> Path: ...

    async def merge_item(self, item_id: str) -> MergeOutcome: ...


@runtime_checkable
class IntegrationLock(Protocol):
    """Serializes concurrent ``build.integrate`` jobs for one
    (project, cycle): the integration branch is a single shared git ref,
    so two workers merging into it at once corrupt each other. A failed
    ``try_acquire`` means another worker holds the branch -- the job
    defers and retries, it never blocks a worker thread waiting."""

    async def try_acquire(self, project_id: UUID, cycle: int) -> bool: ...

    async def release(self, project_id: UUID, cycle: int) -> None: ...


@runtime_checkable
class VerifyWorktrees(Protocol):
    def path_for(self, item_id: str) -> Path: ...


@runtime_checkable
class WorkPlanProducer(Protocol):
    async def decompose(self, spec: DesignSpec) -> tuple[WorkItem, ...]: ...
