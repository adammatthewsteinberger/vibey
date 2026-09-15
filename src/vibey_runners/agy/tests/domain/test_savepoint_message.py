# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Domain tests for savepoint commit message formatting."""

from agyloop.domain.savepoint_message import format_savepoint_commit_message


def test_subject_uses_agyloop_scope_and_headline() -> None:
    subject, body = format_savepoint_commit_message(
        run_id="run-1",
        attempt=3,
        verdict_name="Continue",
        summary="implemented the adapter",
        remaining_work=("write tests",),
        changed_paths=("src/agyloop/foo.py",),
        label="turn",
    )
    assert subject == "chore(agyloop): turn 3 — implemented the adapter"
    assert "Run: run-1" in body
    assert "write tests" in body
    assert "src/agyloop/foo.py" in body


def test_long_subject_is_truncated() -> None:
    subject, _body = format_savepoint_commit_message(
        run_id="run-1",
        attempt=1,
        verdict_name="Done",
        summary="x" * 80,
        remaining_work=(),
        changed_paths=(),
        label="done",
    )
    assert len(subject) <= 72
    assert subject.endswith("…")
