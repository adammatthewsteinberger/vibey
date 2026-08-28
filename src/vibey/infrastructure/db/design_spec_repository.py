# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Cycle-scoped JSON persistence and final context publication for DESIGN specs."""

import json
from dataclasses import asdict
from pathlib import Path
from uuid import UUID

from vibey.application.design_spec import render_design_artifacts
from vibey.domain.spec import (
    AcceptanceCriterion,
    Constraint,
    ConstraintKind,
    DesignSpec,
    NonFunctionalRequirement,
)
from vibey.infrastructure.context_writer import write_context_artifacts
from vibey.infrastructure.db.project_repository import PostgresProjectRepository


class FileDesignSpecRepository:
    def __init__(self, projects: PostgresProjectRepository) -> None:
        self._projects = projects

    async def _path(self, project_id: UUID, cycle: int) -> Path:
        project = await self._projects.get(project_id)
        if project is None:
            raise LookupError(f"unknown project {project_id}")
        return project.repo_path / ".vibey" / "runs" / str(cycle) / "design" / "spec.json"

    async def save(self, project_id: UUID, cycle: int, spec: DesignSpec) -> None:
        path = await self._path(project_id, cycle)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(spec), indent=2) + "\n")

    async def load(self, project_id: UUID, cycle: int) -> DesignSpec | None:
        path = await self._path(project_id, cycle)
        if not path.exists():
            return None
        raw = json.loads(path.read_text())
        return DesignSpec(
            objective=str(raw["objective"]),
            constraints=tuple(
                Constraint(str(item["text"]), ConstraintKind(str(item["kind"])))
                for item in raw["constraints"]
            ),
            non_goals=tuple(str(item) for item in raw["non_goals"]),
            criteria=tuple(AcceptanceCriterion(**item) for item in raw["criteria"]),
            nfrs=tuple(NonFunctionalRequirement(**item) for item in raw["nfrs"]),
            walking_skeleton=str(raw["walking_skeleton"]),
        )

    async def publish(self, project_id: UUID, cycle: int, spec: DesignSpec) -> None:
        path = await self._path(project_id, cycle)
        repo_path = path.parents[4]
        write_context_artifacts(repo_path, render_design_artifacts(spec))
