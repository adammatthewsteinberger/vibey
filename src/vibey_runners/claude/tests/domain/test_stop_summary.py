# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Tests for domain/stop_summary.py — render_stop_summary.

Exercised indirectly by tests/infrastructure/test_control_and_savepoints.py,
but the domain-layer CI gate measures tests/domain/ alone, so the pure
rendering logic (every fallback branch) needs direct coverage here too.
"""

from __future__ import annotations

from claudeloop.domain.stop_summary import StopSummaryInput, render_stop_summary


def _input(**overrides: object) -> StopSummaryInput:
    defaults: dict[str, object] = {
        "run_id": "run-1",
        "session_id": "sess-1",
        "reason": "operator stop",
        "turns_spent": 3,
        "dollars_spent": 1.5,
        "last_summary": "Did the thing.",
        "remaining_plan_items": ("task-a", "task-b"),
        "remaining_work": ("finish x", "review y"),
        "git_changes": "M src/foo.py",
        "latest_savepoint": "refs/claudeloop/run-1/3",
        "events_path": "/tmp/events.jsonl",
        "resume_hint": "claudeloop resume --run-id run-1",
    }
    defaults.update(overrides)
    return StopSummaryInput(**defaults)  # type: ignore[arg-type]


def test_full_summary_includes_every_field() -> None:
    output = render_stop_summary(_input())
    assert "run-1" in output
    assert "operator stop" in output
    assert "`sess-1`" in output
    assert "3" in output and "1.5000" in output
    assert "Did the thing." in output
    assert "M src/foo.py" in output
    assert "- [ ] task-a" in output
    assert "- [ ] task-b" in output
    assert "- finish x" in output
    assert "- review y" in output
    assert "claudeloop resume --run-id run-1" in output
    assert "refs/claudeloop/run-1/3" in output
    assert "/tmp/events.jsonl" in output


def test_falls_back_when_no_plan_checklist_items() -> None:
    output = render_stop_summary(_input(remaining_plan_items=()))
    assert "No checklist items remaining" in output


def test_falls_back_when_no_structured_remaining_work() -> None:
    output = render_stop_summary(_input(remaining_work=()))
    assert "No structured remaining_work reported" in output


def test_falls_back_when_no_savepoint_yet() -> None:
    output = render_stop_summary(_input(latest_savepoint=None))
    assert "No save points created yet" in output


def test_falls_back_when_git_changes_blank() -> None:
    output = render_stop_summary(_input(git_changes="   "))
    assert "No git changes detected for this run" in output


def test_falls_back_when_session_id_unknown() -> None:
    output = render_stop_summary(_input(session_id=None))
    assert "_unknown_" in output


def test_falls_back_when_last_summary_empty() -> None:
    output = render_stop_summary(_input(last_summary=""))
    assert "_none_" in output
