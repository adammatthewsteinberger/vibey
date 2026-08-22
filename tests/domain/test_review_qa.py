# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
from datetime import UTC, datetime
from uuid import uuid4

from vibey.domain.engine import EngineId
from vibey.domain.ledger import EventKind, LedgerEvent, Provenance
from vibey.domain.phase import Phase
from vibey.domain.projections import answer_why_question

NOW = datetime(2026, 8, 15, tzinfo=UTC)


def _make_event(
    kind: EventKind,
    payload: dict[str, object],
    *,
    seq: int = 1,
) -> LedgerEvent:
    return LedgerEvent(
        event_id=uuid4(),
        project_id=uuid4(),
        cycle=1,
        phase=Phase.DESIGN,
        seq=seq,
        kind=kind,
        engine_id=EngineId.CLAUDELOOP,
        job_id=uuid4(),
        causation_id=None,
        correlation_id=uuid4(),
        provenance=Provenance.TRUSTED,
        produced_at=NOW,
        payload=payload,
        digest="abc",
    )


def test_answer_why_question_finds_decision_by_keyword() -> None:
    events = (
        _make_event(
            EventKind.DECISION_RECORDED,
            {
                "decision_id": "dec-1",
                "title": "Use SQLite for local storage",
                "choice": "sqlite",
                "rationale": "Enables zero-dependency local offline usage.",
                "alternatives": ["postgres", "json-files"],
            },
            seq=1,
        ),
        _make_event(
            EventKind.ASSUMPTION_STATED,
            {
                "assumption_id": "assump-1",
                "text": "Target platform is macOS / Linux.",
            },
            seq=2,
        ),
    )

    # Ask why sqlite was chosen
    answer = answer_why_question(events, "Why did you use sqlite?")
    assert "dec-1" in answer
    assert "sqlite" in answer.lower()
    assert "zero-dependency local offline usage" in answer


def test_answer_why_question_finds_assumption() -> None:
    events = (
        _make_event(
            EventKind.ASSUMPTION_STATED,
            {
                "assumption_id": "assump-1",
                "text": "Target platform is macOS / Linux.",
            },
            seq=1,
        ),
    )

    answer = answer_why_question(events, "Why target macOS?")
    assert "assump-1" in answer
    assert "Target platform is macOS / Linux" in answer


def test_answer_why_question_fallback_summarizes_available_ledger_context() -> None:
    events = (
        _make_event(
            EventKind.DECISION_RECORDED,
            {
                "decision_id": "dec-2",
                "title": "Use Typer for CLI",
                "choice": "typer",
                "rationale": "Type-safe CLI argument parsing.",
            },
            seq=1,
        ),
    )

    answer = answer_why_question(events, "Why something completely unrelated?")
    assert "dec-2" in answer
    assert "typer" in answer.lower()


def test_answer_why_question_empty_ledger() -> None:
    answer = answer_why_question((), "Why anything?")
    assert "No decisions or assumptions recorded" in answer
