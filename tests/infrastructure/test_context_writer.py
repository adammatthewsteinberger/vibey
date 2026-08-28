# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from pathlib import Path

from vibey.infrastructure.context_writer import write_context_artifacts


def test_writes_context_artifacts_and_is_idempotent(tmp_path: Path) -> None:
    artifacts = {"spec.md": "# Spec\n", "acceptance.md": "# Acceptance\n"}
    written = write_context_artifacts(tmp_path, artifacts)
    assert written == (
        tmp_path / ".vibey/context/spec.md",
        tmp_path / ".vibey/context/acceptance.md",
    )
    assert written[0].read_text() == "# Spec\n"
    assert write_context_artifacts(tmp_path, artifacts) == ()


def test_rejects_artifact_names_that_escape_context(tmp_path: Path) -> None:
    try:
        write_context_artifacts(tmp_path, {"../secret": "bad"})
    except ValueError as exc:
        assert "filename" in str(exc)
    else:
        raise AssertionError("expected unsafe artifact name rejection")
