# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
from datetime import UTC, datetime

from vibey.application.text_verdict_fallback import extract_verdict_from_text
from vibey.application.verdict_extraction import extract_events

NOW = datetime(2026, 1, 1, tzinfo=UTC)

FREE_TEXT_TURN = """
Added the outbox table and the writer; relay is stubbed.
Question: Should retries be capped or unbounded?
Decision: Outbox over 2PC because single local transaction, no XA coordinator
Assumption: Postgres is the only write DB
Remaining: wire the retry policy into the outbox relay
"""

COMPLETE_TEXT_TURN = """
Implemented the retry cap at 5 attempts.
Decision: Retry cap at 5 attempts because it matches the SLA
Done.
"""

BARE_TEXT_TURN = "Just some free-form notes with no structure at all."


def test_extracted_schema_has_the_same_shape_as_structured_output() -> None:
    verdict = extract_verdict_from_text(FREE_TEXT_TURN)

    for key in (
        "complete",
        "remaining_work",
        "blocked_on",
        "summary",
        "questions",
        "decisions",
        "assumptions",
        "artifacts",
    ):
        assert key in verdict


def test_question_prefix_is_recognized() -> None:
    verdict = extract_verdict_from_text(FREE_TEXT_TURN)
    assert verdict["questions"] == [
        {"text": "Should retries be capped or unbounded?", "blocking": False}
    ]


def test_decision_prefix_splits_choice_and_rationale() -> None:
    verdict = extract_verdict_from_text(FREE_TEXT_TURN)
    assert verdict["decisions"][0]["title"] == "Outbox over 2PC"
    assert verdict["decisions"][0]["rationale"] == "single local transaction, no XA coordinator"


def test_assumption_prefix_is_recognized() -> None:
    verdict = extract_verdict_from_text(FREE_TEXT_TURN)
    assert verdict["assumptions"] == [
        {"text": "Postgres is the only write DB", "confidence": "medium"}
    ]


def test_remaining_prefix_populates_remaining_work() -> None:
    verdict = extract_verdict_from_text(FREE_TEXT_TURN)
    assert verdict["remaining_work"] == ["wire the retry policy into the outbox relay"]


def test_unstructured_lines_become_the_summary() -> None:
    verdict = extract_verdict_from_text(FREE_TEXT_TURN)
    assert "Added the outbox table and the writer; relay is stubbed." in verdict["summary"]


def test_done_marker_sets_complete_true() -> None:
    verdict = extract_verdict_from_text(COMPLETE_TEXT_TURN)
    assert verdict["complete"] is True


def test_no_done_marker_leaves_complete_false() -> None:
    verdict = extract_verdict_from_text(FREE_TEXT_TURN)
    assert verdict["complete"] is False


def test_bare_text_with_no_prefixes_still_produces_a_valid_schema() -> None:
    verdict = extract_verdict_from_text(BARE_TEXT_TURN)
    assert verdict["questions"] == []
    assert verdict["decisions"] == []
    assert verdict["summary"] == BARE_TEXT_TURN.strip()


def test_fallback_output_feeds_directly_into_extract_events() -> None:
    """The point of matching the schema exactly: extract_events() must not
    need to know whether a verdict came from structured output or the
    text fallback."""
    verdict = extract_verdict_from_text(FREE_TEXT_TURN)
    result = extract_events(verdict, open_items=(), now=NOW)

    kinds = [e.kind for e in result.events]
    assert kinds == ["QuestionAsked", "DecisionRecorded", "AssumptionStated", "VerdictRendered"]


def test_a_blocked_line_becomes_blocked_on() -> None:
    """The one label that changes the verdict rather than adding to a list: a
    blocked turn must not be read as merely incomplete."""
    verdict = extract_verdict_from_text(
        "Summary of what happened.\nBlocked: waiting on the staging credentials\n"
    )

    assert verdict["blocked_on"] == "waiting on the staging credentials"
    assert verdict["complete"] is False


def test_a_remaining_line_is_collected_without_blocking() -> None:
    verdict = extract_verdict_from_text("Remaining: wire the retry cap\n")

    assert verdict["remaining_work"] == ["wire the retry cap"]
    assert verdict["blocked_on"] is None
