"""Phase 2 collaborators: worktrees, provisioning, budget, gates, integration."""

from __future__ import annotations

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
class VerifyWorktrees(Protocol):
    def path_for(self, item_id: str) -> Path: ...


@runtime_checkable
class WorkPlanProducer(Protocol):
    async def decompose(self, spec: DesignSpec) -> tuple[WorkItem, ...]: ...
