from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from vibey.application.dto import ProjectRecord
from vibey.domain.phase import Phase
from vibey.infrastructure.review_artifact_writer import FileReviewArtifactWriter

NOW = datetime(2026, 8, 15, tzinfo=UTC)


class FakeProjectRepo:
    def __init__(self, project: ProjectRecord | None = None) -> None:
        self.project = project

    async def get(self, project_id: object) -> ProjectRecord | None:
        return self.project


async def test_file_review_artifact_writer(tmp_path: Path) -> None:
    project_id = uuid4()
    proj = ProjectRecord(
        project_id=project_id,
        name="test-proj",
        repo_path=tmp_path,
        phase=Phase.REVIEW,
        cycle=1,
        max_cycles=5,
        config={},
        created_at=NOW,
        updated_at=NOW,
    )
    writer = FileReviewArtifactWriter(FakeProjectRepo(proj))
    written = await writer.write_review_artifacts(
        project_id,
        1,
        {"DEMO.md": "# Demo", "run-it.sh": "#!/bin/bash\necho ok"},
        executable=["run-it.sh"],
    )

    demo_path = tmp_path / ".vibey" / "runs" / "1" / "review" / "DEMO.md"
    run_it_path = tmp_path / ".vibey" / "runs" / "1" / "review" / "run-it.sh"

    assert written["DEMO.md"] == demo_path
    assert written["run-it.sh"] == run_it_path
    assert demo_path.exists()
    assert demo_path.read_text() == "# Demo"
    assert run_it_path.exists()
    assert run_it_path.stat().st_mode & 0o111  # executable


async def test_file_review_artifact_writer_unknown_project(tmp_path: Path) -> None:
    writer = FileReviewArtifactWriter(FakeProjectRepo(None))
    with pytest.raises(LookupError):
        await writer.write_review_artifacts(uuid4(), 1, {"DEMO.md": "# Demo"})

    writer_no_get = FileReviewArtifactWriter(object())
    with pytest.raises(LookupError):
        await writer_no_get.write_review_artifacts(uuid4(), 1, {"DEMO.md": "# Demo"})
