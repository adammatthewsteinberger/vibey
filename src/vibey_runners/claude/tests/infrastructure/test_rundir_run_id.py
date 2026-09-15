# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Caller-supplied run ids: validation and collision behaviour."""

from __future__ import annotations

from pathlib import Path

import pytest

from claudeloop.infrastructure.rundir import RunDirectory, validate_run_id


def test_validate_run_id_rejects_path_traversal() -> None:
    """A supplied run id becomes a path segment; it must never escape runs/."""
    for bad in (
        "../escape",
        "/abs/path",
        "a/b",
        "..",
        ".hidden",
        "",
        "   ",
        "has space",
        "a" * 200,
    ):
        with pytest.raises(ValueError):
            validate_run_id(bad)


def test_validate_run_id_accepts_orchestrator_style_ids() -> None:
    for good in ("vibey-item-7", "20260815T101112Z-abc123", "a", "A.b_c-1"):
        assert validate_run_id(good) == good
    assert validate_run_id("  padded  ") == "padded"


def test_create_uses_a_supplied_run_id(tmp_path: Path) -> None:
    directory = RunDirectory.create(tmp_path / "runs", cwd=tmp_path, run_id="vibey-item-7")
    assert directory.root.name == "vibey-item-7"
    assert directory.read_meta().run_id == "vibey-item-7"


def test_create_still_mints_an_id_when_none_is_supplied(tmp_path: Path) -> None:
    directory = RunDirectory.create(tmp_path / "runs", cwd=tmp_path)
    assert directory.root.name != ""
    assert directory.read_meta().run_id == directory.root.name


def test_create_refuses_to_reuse_a_run_id(tmp_path: Path) -> None:
    RunDirectory.create(tmp_path / "runs", cwd=tmp_path, run_id="taken")
    with pytest.raises(FileExistsError):
        RunDirectory.create(tmp_path / "runs", cwd=tmp_path, run_id="taken")


def test_create_rejects_a_traversing_run_id(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        RunDirectory.create(tmp_path / "runs", cwd=tmp_path, run_id="../../escape")
    assert not (tmp_path.parent / "escape").exists()
