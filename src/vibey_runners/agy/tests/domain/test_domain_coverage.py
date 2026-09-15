# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from agyloop.domain.classify import (
    QuotaViolation,
    _window_kind_from_violations,
    looks_like_withdrawn_model,
)
from agyloop.domain.pricing import price_for_model
from agyloop.domain.savepoint_message import format_savepoint_commit_message


def test_looks_like_withdrawn_model_edge_cases() -> None:
    assert not looks_like_withdrawn_model(None)
    assert not looks_like_withdrawn_model("")
    assert looks_like_withdrawn_model("Error 404: Not Found")
    assert looks_like_withdrawn_model("status code 404")
    assert looks_like_withdrawn_model("RESOURCE_EXHAUSTED: RPC status NOT_FOUND")


def test_window_kind_from_violations_loop_and_none() -> None:
    # First violation has unknown quota metric/id, second has known
    v1 = QuotaViolation(quota_metric="unknown_metric", quota_id="unknown_id")
    v2 = QuotaViolation(quota_metric="queries_per_minute", quota_id="rpm")
    assert _window_kind_from_violations((v1, v2)) == "rpm"

    # All unknown
    assert _window_kind_from_violations((v1,)) is None


def test_price_for_model_prefix_and_substring() -> None:
    # Key that starts with known or has known in key
    inn, out = price_for_model("gemini-2.5-pro-preview-0501")
    assert inn > 0


def test_savepoint_commit_message_empty_summary_and_fallbacks() -> None:
    # Blank lines in summary before content
    subject, _ = format_savepoint_commit_message(
        run_id="run-1",
        attempt=1,
        verdict_name="Continue",
        summary="\n  \nfirst actual line\nsecond line",
        remaining_work=(),
        changed_paths=(),
        label="turn",
    )
    assert "first actual line" in subject

    # Empty summary with changed paths
    subject, _ = format_savepoint_commit_message(
        run_id="run-1",
        attempt=1,
        verdict_name="Continue",
        summary="   \n  ",
        remaining_work=(),
        changed_paths=("src/agyloop/bar.py",),
        label="turn",
    )
    assert "bar.py" in subject

    # Empty summary, empty changed paths
    subject, _ = format_savepoint_commit_message(
        run_id="run-1",
        attempt=1,
        verdict_name="Continue",
        summary="",
        remaining_work=(),
        changed_paths=(),
        label="turn",
    )
    assert "workspace checkpoint" in subject

    # Empty summary, slash-only changed path
    subject, _ = format_savepoint_commit_message(
        run_id="run-1",
        attempt=1,
        verdict_name="Continue",
        summary="",
        remaining_work=(),
        changed_paths=("///",),
        label="turn",
    )
    assert "workspace checkpoint" in subject
