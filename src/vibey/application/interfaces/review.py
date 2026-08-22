# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Phase 3 collaborators: automated review and artifact writing."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable
from uuid import UUID

from vibey.domain.review import Ambiguity, Severity


@dataclass(frozen=True, slots=True)
class AutomatedFinding:
    category: str
    text: str
    severity: Severity = Severity.MEDIUM
    ambiguity: Ambiguity = Ambiguity.CLEAR
    finding_id: str | None = None


@runtime_checkable
class AutomatedReviewRunner(Protocol):
    async def run_automated_reviews(
        self, project_id: UUID, cycle: int
    ) -> tuple[AutomatedFinding, ...]: ...


@runtime_checkable
class ReviewArtifactWriter(Protocol):
    async def write_review_artifacts(
        self,
        project_id: UUID,
        cycle: int,
        artifacts: Mapping[str, str],
        *,
        executable: Sequence[str] = (),
    ) -> Mapping[str, Path]: ...
