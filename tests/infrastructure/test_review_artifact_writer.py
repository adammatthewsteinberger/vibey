# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
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


async def test_file_review_artifact_writer_cycle_isolation(tmp_path: Path) -> None:
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

    # Write cycle 1
    await writer.write_review_artifacts(
        project_id,
        1,
        {"DEMO.md": "# Demo Cycle 1", "deltas.md": "# Deltas Cycle 1"},
    )

    # Write cycle 2
    await writer.write_review_artifacts(
        project_id,
        2,
        {"DEMO.md": "# Demo Cycle 2", "deltas.md": "# Deltas Cycle 2"},
    )

    c1_demo = tmp_path / ".vibey" / "runs" / "1" / "review" / "DEMO.md"
    c2_demo = tmp_path / ".vibey" / "runs" / "2" / "review" / "DEMO.md"

    # Cycle 1 is preserved and not overwritten
    assert c1_demo.exists()
    assert c1_demo.read_text() == "# Demo Cycle 1"

    # Cycle 2 has its own isolated content
    assert c2_demo.exists()
    assert c2_demo.read_text() == "# Demo Cycle 2"


async def test_file_review_artifact_writer_unknown_project(tmp_path: Path) -> None:
    writer = FileReviewArtifactWriter(FakeProjectRepo(None))
    with pytest.raises(LookupError):
        await writer.write_review_artifacts(uuid4(), 1, {"DEMO.md": "# Demo"})

    writer_no_get = FileReviewArtifactWriter(object())
    with pytest.raises(LookupError):
        await writer_no_get.write_review_artifacts(uuid4(), 1, {"DEMO.md": "# Demo"})
