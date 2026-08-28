# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Filesystem writer for Phase 3 REVIEW artifacts."""

from collections.abc import Mapping, Sequence
from pathlib import Path
from uuid import UUID

from vibey.application.interfaces import (
    ProjectStore,
)


class FileReviewArtifactWriter:
    def __init__(self, projects: ProjectStore | object) -> None:
        self._projects = projects

    async def _get_repo_path(self, project_id: UUID) -> Path:
        if hasattr(self._projects, "get"):
            proj = await self._projects.get(project_id)
            if proj is None:
                raise LookupError(f"unknown project {project_id}")
            return Path(proj.repo_path)
        raise LookupError(f"cannot resolve repo path for {project_id}")

    async def write_review_artifacts(
        self,
        project_id: UUID,
        cycle: int,
        artifacts: Mapping[str, str],
        *,
        executable: Sequence[str] = (),
    ) -> Mapping[str, Path]:
        repo_path = await self._get_repo_path(project_id)
        review_dir = repo_path / ".vibey" / "runs" / str(cycle) / "review"
        review_dir.mkdir(parents=True, exist_ok=True)
        written: dict[str, Path] = {}
        for rel_name, content in artifacts.items():
            path = review_dir / rel_name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            if rel_name in executable:
                path.chmod(path.stat().st_mode | 0o111)
            written[rel_name] = path
        return written
