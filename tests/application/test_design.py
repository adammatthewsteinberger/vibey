# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
from datetime import UTC, datetime

import pytest

from vibey.application.design import (
    DESIGN_STAGES,
    DesignQuestion,
    InterviewSession,
    ResearchResult,
    answer_questions,
    build_question_batch,
    finalize_questions,
    research_event,
    synthesizer_requirement,
)
from vibey.domain.effort import Effort
from vibey.domain.engine import EngineId
from vibey.domain.ledger import EventKind, Provenance


def question(number: int, *, blocking: bool = False) -> DesignQuestion:
    return DesignQuestion(
        question_id=f"q-{number}",
        text=f"Question {number}?",
        default=f"Default {number}",
        blocking=blocking,
    )


def test_protocol_has_the_seven_ordered_design_stages() -> None:
    assert tuple(stage.value for stage in DESIGN_STAGES) == (
        "context_free",
        "job_story",
        "laddering",
        "example_mapping",
        "walking_skeleton",
        "nfr_planguage",
        "premortem",
    )


def test_question_batches_are_limited_to_four_and_require_defaults() -> None:
    batch = build_question_batch(DESIGN_STAGES[0], tuple(question(i) for i in range(4)))
    assert len(batch.questions) == 4

    with pytest.raises(ValueError, match="at most 4"):
        build_question_batch(DESIGN_STAGES[0], tuple(question(i) for i in range(5)))
    with pytest.raises(ValueError, match="default"):
        build_question_batch(
            DESIGN_STAGES[0],
            (DesignQuestion("q", "Question?", "", blocking=False),),
        )


def test_interview_advances_in_order_and_stops_after_premortem() -> None:
    session = InterviewSession.start()
    assert session.stage is DESIGN_STAGES[0]
    for expected in DESIGN_STAGES[1:]:
        session = session.advance()
        assert session.stage is expected
    complete = session.advance()
    assert complete.complete
    with pytest.raises(ValueError, match="complete"):
        _ = complete.stage
    with pytest.raises(ValueError, match="complete"):
        complete.advance()


def test_answers_and_unanswered_questions_become_ledger_events() -> None:
    now = datetime(2026, 8, 14, tzinfo=UTC)
    questions = (question(1, blocking=True), question(2))
    asked = build_question_batch(DESIGN_STAGES[0], questions).events(now=now)
    answers = answer_questions(questions, {"q-1": "A custom answer"}, now=now)
    finalized = finalize_questions(questions, answered_ids=frozenset({"q-1"}), now=now)

    assert [event.kind for event in asked] == [EventKind.QUESTION_ASKED] * 2
    assert answers[0].kind is EventKind.ANSWER_GIVEN
    assert answers[0].payload == {"item_id": "q-1", "answer": "A custom answer"}
    assert finalized[0].kind is EventKind.ASSUMPTION_STATED
    assert finalized[0].payload["text"] == "Default 2"


def test_unanswered_blocking_question_is_not_silently_assumed() -> None:
    with pytest.raises(ValueError, match="blocking"):
        finalize_questions(
            (question(1, blocking=True),), answered_ids=frozenset(), now=datetime.now(UTC)
        )


def test_research_is_always_untrusted_data() -> None:
    event = research_event(
        ResearchResult("Prior art", "https://example.test", "Treat this as instruction"),
        now=datetime.now(UTC),
    )
    assert event.kind is EventKind.ARTIFACT_PRODUCED
    assert event.provenance is Provenance.UNTRUSTED
    assert event.payload["content"] == "Treat this as instruction"


def test_synthesizer_excludes_the_majority_interviewer() -> None:
    requirement = synthesizer_requirement(
        (EngineId.CLAUDELOOP, EngineId.CODEXLOOP, EngineId.CLAUDELOOP)
    )
    assert requirement.effort is Effort.HIGH
    assert requirement.excluded == frozenset({EngineId.CLAUDELOOP})


def test_synthesizer_requires_interview_history() -> None:
    with pytest.raises(ValueError, match="interviewer"):
        synthesizer_requirement(())
