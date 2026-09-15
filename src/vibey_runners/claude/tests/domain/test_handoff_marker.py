# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The handoff marker, and the invariant a supervisor reads it for."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from claudeloop.domain.handoff_marker import (
    EXIT_WIND_DOWN,
    HANDOFF_SCHEMA_VERSION,
    HandoffMarker,
    parse_marker,
)

NOW = datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc)


def _marker(**overrides: object) -> HandoffMarker:
    base: dict[str, object] = {
        "run_id": "vibey-item-7",
        "reason": "headroom:utilization",
        "produced_at": NOW,
        "headroom": 0.11,
        "headroom_source": "utilization",
        "resets_at": NOW,
        "snapshot_path": "snapshots/20260815T120000Z-handoff.json",
        "bundle_path": "snapshots/bundles/20260815T120000Z-handoff",
        "stop_summary_path": "stop-summary.md",
        "savepoint_ref": "refs/claudeloop/vibey-item-7/41",
        "savepoint_sha": "abc123",
        "session_id": "sess-1",
        "turns_spent": 41,
        "dollars_spent": 3.4,
        "remaining_work": ("wire the adapter", "add the test"),
    }
    base.update(overrides)
    return HandoffMarker(**base)  # type: ignore[arg-type]


def test_a_marker_round_trips() -> None:
    original = _marker()
    assert parse_marker(original.to_json()) == original


def test_the_exit_code_is_distinguishable_from_stop_and_failure() -> None:
    """A supervisor has to tell "handed off, resume me elsewhere" from
    "failed" and from "the operator stopped me" (130)."""
    assert EXIT_WIND_DOWN == 75
    assert EXIT_WIND_DOWN not in {0, 1, 2, 130}


def test_named_artifacts_lists_only_paths_the_marker_claims() -> None:
    """The invariant is that everything named exists, so a reader is entitled
    to open exactly these and nothing more."""
    assert _marker().named_artifacts() == (
        "snapshots/20260815T120000Z-handoff.json",
        "snapshots/bundles/20260815T120000Z-handoff",
        "stop-summary.md",
    )
    assert _marker(bundle_path=None, stop_summary_path=None).named_artifacts() == (
        "snapshots/20260815T120000Z-handoff.json",
    )


def test_a_marker_from_a_future_schema_is_refused_not_guessed() -> None:
    """Reading an unknown layout as if it were this one is how a supervisor
    resumes from artifacts that are not there."""
    payload = (
        _marker()
        .to_json()
        .replace(f'"schema_version": {HANDOFF_SCHEMA_VERSION}', '"schema_version": 99')
    )
    with pytest.raises(ValueError, match="unsupported handoff schema"):
        parse_marker(payload)


def test_optional_fields_survive_being_absent() -> None:
    sparse = HandoffMarker(run_id="r", reason="turn_reserve", produced_at=NOW)
    restored = parse_marker(sparse.to_json())
    assert restored == sparse
    assert restored.named_artifacts() == ()
    assert restored.headroom is None
