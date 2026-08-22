# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Cycle-scoped JSON persistence and context publication for VisualInventory."""

import json
from dataclasses import asdict
from pathlib import Path
from uuid import UUID

from vibey.application.visual_spec import render_visual_artifacts
from vibey.domain.visual import (
    MediaManifestEntry,
    MediaModality,
    ScreenSurface,
    SurfaceAction,
    VisualInventory,
)
from vibey.infrastructure.db.project_repository import PostgresProjectRepository


def _write_visual_context_artifacts(repo_path: Path, artifacts: dict[str, str]) -> None:
    context_dir = repo_path / ".vibey" / "context" / "visual"
    context_dir.mkdir(parents=True, exist_ok=True)
    for name, content in artifacts.items():
        (context_dir / name).write_text(content)


class FileVisualInventoryRepository:
    def __init__(self, projects: PostgresProjectRepository) -> None:
        self._projects = projects

    async def _path(self, project_id: UUID, cycle: int) -> Path:
        project = await self._projects.get(project_id)
        if project is None:
            raise LookupError(f"unknown project {project_id}")
        return project.repo_path / ".vibey" / "runs" / str(cycle) / "visual" / "inventory.json"

    async def save(self, project_id: UUID, cycle: int, inventory: VisualInventory) -> None:
        path = await self._path(project_id, cycle)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(inventory), indent=2) + "\n")

    async def load(self, project_id: UUID, cycle: int) -> VisualInventory | None:
        path = await self._path(project_id, cycle)
        if not path.exists():
            return None
        raw = json.loads(path.read_text())
        return VisualInventory(
            surfaces=tuple(
                ScreenSurface(
                    screen_id=str(surface["screen_id"]),
                    name=str(surface["name"]),
                    action=SurfaceAction(str(surface["action"])),
                    responsive_states=tuple(str(s) for s in surface["responsive_states"]),
                    accessibility_requirements=tuple(
                        str(s) for s in surface["accessibility_requirements"]
                    ),
                    media_manifest=tuple(
                        MediaManifestEntry(
                            asset_key=str(entry["asset_key"]),
                            modality=MediaModality(str(entry["modality"])),
                            prompt=str(entry["prompt"]),
                        )
                        for entry in surface["media_manifest"]
                    ),
                )
                for surface in raw["surfaces"]
            )
        )

    async def publish(self, project_id: UUID, cycle: int, inventory: VisualInventory) -> None:
        project = await self._projects.get(project_id)
        if project is None:
            raise LookupError(f"unknown project {project_id}")
        _write_visual_context_artifacts(project.repo_path, render_visual_artifacts(inventory))
