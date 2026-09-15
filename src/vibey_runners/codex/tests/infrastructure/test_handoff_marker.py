# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Handoff marker write: tmp-file + os.replace ensures crash-safety."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from codexloop.domain.handoff_marker import HANDOFF_MARKER_FILENAME, HandoffMarker, parse_marker
from codexloop.infrastructure.rundir import write_handoff_marker


def test_write_handoff_marker_writes_to_run_root(tmp_path: Path) -> None:
    """Marker is written to runs/<run_id>/handoff.json."""
    run_root = tmp_path / ".codexloop" / "runs" / "test-run"
    run_root.mkdir(parents=True, exist_ok=True)

    marker = HandoffMarker(
        run_id="test-run",
        reason="test",
        produced_at=datetime.now(UTC),
        session_id="thread-1",
        turns_spent=5,
        dollars_spent=1.50,
        remaining_work=("task 1", "task 2"),
    )

    write_handoff_marker(run_root, marker)

    marker_path = run_root / HANDOFF_MARKER_FILENAME
    assert marker_path.is_file()

    # Verify content round-trips
    parsed = parse_marker(marker_path.read_text(encoding="utf-8"))
    assert parsed.run_id == marker.run_id
    assert parsed.reason == marker.reason
    assert parsed.session_id == marker.session_id
    assert parsed.turns_spent == marker.turns_spent
    assert abs(parsed.dollars_spent - marker.dollars_spent) < 0.01
    assert parsed.remaining_work == marker.remaining_work


def test_write_handoff_marker_uses_temp_file_then_rename(tmp_path: Path) -> None:
    """Uses temp file + os.replace for atomic write."""
    run_root = tmp_path / ".codexloop" / "runs" / "test-run"
    run_root.mkdir(parents=True, exist_ok=True)
    marker = HandoffMarker(
        run_id="test-run",
        reason="atomic test",
        produced_at=datetime.now(UTC),
    )

    # Patch os.replace to verify it's called
    with patch("os.replace") as mock_replace:
        write_handoff_marker(run_root, marker)

        # Verify os.replace was called
        assert mock_replace.call_count == 1
        call_args = mock_replace.call_args[0]

        # First arg is temp file (should have .tmp suffix)
        temp_path = Path(call_args[0])
        assert temp_path.name.endswith(".tmp")

        # Second arg is final destination
        final_path = Path(call_args[1])
        assert final_path.name == HANDOFF_MARKER_FILENAME


def test_write_handoff_marker_preserves_prior_file_on_failure(tmp_path: Path) -> None:
    """If write fails mid-way, the existing marker is left intact."""
    run_root = tmp_path / ".codexloop" / "runs" / "test-run"
    run_root.mkdir(parents=True, exist_ok=True)
    marker_path = run_root / HANDOFF_MARKER_FILENAME

    # Write an initial marker
    initial_marker = HandoffMarker(
        run_id="test-run",
        reason="initial",
        produced_at=datetime.now(UTC),
        turns_spent=3,
    )
    write_handoff_marker(run_root, initial_marker)
    initial_content = marker_path.read_text(encoding="utf-8")
    assert "initial" in initial_content

    # Simulate a failure during write by making os.replace raise
    new_marker = HandoffMarker(
        run_id="test-run",
        reason="new",
        produced_at=datetime.now(UTC),
        turns_spent=5,
    )

    with (
        patch("os.replace", side_effect=OSError("disk full")),
        pytest.raises(OSError, match="disk full"),
    ):
        write_handoff_marker(run_root, new_marker)

    # Verify original file is still intact
    preserved_content = marker_path.read_text(encoding="utf-8")
    assert preserved_content == initial_content
    assert "initial" in preserved_content
    assert "new" not in preserved_content


def test_write_handoff_marker_overwrites_existing_marker(tmp_path: Path) -> None:
    """Subsequent writes replace the previous marker."""
    run_root = tmp_path / ".codexloop" / "runs" / "test-run"
    run_root.mkdir(parents=True, exist_ok=True)

    first = HandoffMarker(
        run_id="test-run",
        reason="first",
        produced_at=datetime.now(UTC),
        turns_spent=1,
    )
    write_handoff_marker(run_root, first)

    second = HandoffMarker(
        run_id="test-run",
        reason="second",
        produced_at=datetime.now(UTC),
        turns_spent=2,
    )
    write_handoff_marker(run_root, second)

    marker_path = run_root / HANDOFF_MARKER_FILENAME
    content = marker_path.read_text(encoding="utf-8")
    data = json.loads(content)
    assert data["reason"] == "second"
    assert data["turns_spent"] == 2
    assert "first" not in content
