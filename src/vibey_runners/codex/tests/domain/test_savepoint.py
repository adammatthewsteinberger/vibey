# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Domain save-point value objects and commit message formatting."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from codexloop.domain.savepoint import SavePointRef
from codexloop.domain.savepoint_message import format_savepoint_commit_message


def test_savepoint_ref_rejects_invalid_fields() -> None:
    at = datetime(2026, 8, 13, tzinfo=UTC)
    with pytest.raises(ValueError, match=">= 1"):
        SavePointRef(n=0, ref="refs/x", sha="abc", label="t", at=at)
    with pytest.raises(ValueError, match="blank"):
        SavePointRef(n=1, ref="  ", sha="abc", label="t", at=at)
    with pytest.raises(ValueError, match="blank"):
        SavePointRef(n=1, ref="refs/x", sha=" ", label="t", at=at)


def test_savepoint_message_truncates_long_subject() -> None:
    subject, _body = format_savepoint_commit_message(
        run_id="run-1",
        attempt=1,
        verdict_name="Continue",
        summary="x" * 120,
    )
    assert len(subject) <= 72
    assert subject.endswith("…")


def test_savepoint_message_headline_from_paths_and_default() -> None:
    subject_paths, body = format_savepoint_commit_message(
        run_id="run-1",
        attempt=2,
        verdict_name="Continue",
        summary="\n\n",
        changed_paths=("src/deep/file.py",),
        remaining_work=("finish auth",),
    )
    assert "file.py" in subject_paths
    assert "finish auth" in body

    subject_default, body_default = format_savepoint_commit_message(
        run_id="run-2",
        attempt=3,
        verdict_name="Done",
        summary="",
    )
    assert "workspace checkpoint" in subject_default
    assert "- (none)" in body_default

    subject_slash, _ = format_savepoint_commit_message(
        run_id="run-3",
        attempt=4,
        verdict_name="Continue",
        summary="",
        changed_paths=("/",),
    )
    assert "workspace checkpoint" in subject_slash
