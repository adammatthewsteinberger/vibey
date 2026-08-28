# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from datetime import UTC, datetime

from vibey.application.verdict_extraction import (
    OpenItemKind,
    OpenItemRef,
    extract_events,
    normalize_text,
)

NOW = datetime(2026, 1, 1, tzinfo=UTC)

# The example verdict schema from handoff-protocol.md §3.3, reused as the
# fixture turn for extraction.
SAMPLE_VERDICT = {
    "complete": False,
    "remaining_work": ["wire the retry policy into the outbox relay"],
    "blocked_on": None,
    "summary": "Added the outbox table and the writer; relay is stubbed.",
    "questions": [{"text": "Should retries be capped or unbounded?", "blocking": False}],
    "decisions": [
        {
            "title": "Outbox over 2PC",
            "choice": "transactional outbox",
            "rationale": "single local transaction; no XA coordinator",
            "alternatives": ["two-phase commit", "dual write"],
        }
    ],
    "assumptions": [{"text": "Postgres is the only write DB", "confidence": "high"}],
    "artifacts": [{"kind": "migration", "path": "migrations/007_outbox.sql"}],
}


def test_normalize_text_lowercases_and_strips_punctuation() -> None:
    assert normalize_text("Should retries be capped, or UNBOUNDED?!") == (
        "should retries be capped or unbounded"
    )


def test_normalize_text_collapses_whitespace() -> None:
    assert normalize_text("hello    world\n\tfoo") == "hello world foo"


def test_extraction_mints_ids_for_every_closable_kind() -> None:
    result = extract_events(SAMPLE_VERDICT, open_items=(), now=NOW)

    kinds = [e.kind for e in result.events]
    assert kinds == [
        "QuestionAsked",
        "DecisionRecorded",
        "AssumptionStated",
        "ArtifactProduced",
        "VerdictRendered",
    ]

    question_event = result.events[0]
    assert question_event.payload["question_id"].startswith("q_")
    decision_event = result.events[1]
    assert decision_event.payload["decision_id"].startswith("d_")
    assumption_event = result.events[2]
    assert assumption_event.payload["assumption_id"].startswith("a_")


def test_verdict_rendered_carries_remaining_work_and_summary() -> None:
    result = extract_events(SAMPLE_VERDICT, open_items=(), now=NOW)

    verdict_event = next(e for e in result.events if e.kind == "VerdictRendered")
    assert verdict_event.payload["remaining_work"] == [
        "wire the retry policy into the outbox relay"
    ]
    assert verdict_event.payload["complete"] is False


def test_restating_an_open_question_does_not_mint_a_second_id() -> None:
    """The milestone's own done-when condition, verbatim."""
    open_items = (
        OpenItemRef(
            item_id="q_existing1",
            kind=OpenItemKind.QUESTION,
            normalized=normalize_text("Should retries be capped or unbounded?"),
        ),
    )

    reworded_verdict = {
        **SAMPLE_VERDICT,
        "questions": [{"text": "should retries be capped, or unbounded???", "blocking": False}],
    }

    result = extract_events(reworded_verdict, open_items=open_items, now=NOW)

    question_events = [e for e in result.events if e.kind == "QuestionAsked"]
    assert question_events == []
    assert result.reused_ids["should retries be capped, or unbounded???"] == "q_existing1"


def test_a_genuinely_new_question_still_mints_an_id_even_with_other_items_open() -> None:
    open_items = (
        OpenItemRef(
            item_id="q_existing1", kind=OpenItemKind.QUESTION, normalized="an unrelated question"
        ),
    )

    result = extract_events(SAMPLE_VERDICT, open_items=open_items, now=NOW)

    question_events = [e for e in result.events if e.kind == "QuestionAsked"]
    assert len(question_events) == 1
    assert question_events[0].payload["question_id"] != "q_existing1"


def test_dedup_only_matches_within_the_same_kind() -> None:
    """A decision and a question that happen to normalize to the same text
    must not be deduped against each other."""
    open_items = (
        OpenItemRef(
            item_id="d_existing1",
            kind=OpenItemKind.DECISION,
            normalized=normalize_text("Should retries be capped or unbounded?"),
        ),
    )

    result = extract_events(SAMPLE_VERDICT, open_items=open_items, now=NOW)

    question_events = [e for e in result.events if e.kind == "QuestionAsked"]
    assert len(question_events) == 1


def test_empty_verdict_still_produces_a_verdict_rendered_event() -> None:
    result = extract_events({}, open_items=(), now=NOW)
    assert [e.kind for e in result.events] == ["VerdictRendered"]


def test_malformed_list_fields_are_ignored_not_raised() -> None:
    malformed = {"questions": "not-a-list", "decisions": [42, {"title": "ok", "choice": "x"}]}
    result = extract_events(malformed, open_items=(), now=NOW)

    decision_events = [e for e in result.events if e.kind == "DecisionRecorded"]
    assert len(decision_events) == 1
    assert decision_events[0].payload["title"] == "ok"


# --- per-engine fixture turns (4.4's "per-engine fixtures") ------------------

CLAUDELOOP_TURN = SAMPLE_VERDICT

CODEXLOOP_TURN = {
    "complete": True,
    "remaining_work": [],
    "summary": "Implemented the retry cap at 5 attempts.",
    "questions": [],
    "decisions": [
        {
            "title": "Retry cap",
            "choice": "5 attempts",
            "rationale": "matches SLA",
            "alternatives": [],
        }
    ],
    "assumptions": [],
    "artifacts": [{"kind": "diff", "path": "relay.py"}],
}

CURSORLOOP_TURN = {
    "complete": False,
    "remaining_work": ["unflake the CI test"],
    "summary": "Investigated CI flake.",
    "questions": [{"text": "Is the flake timing-related?", "blocking": True}],
    "decisions": [],
    "assumptions": [{"text": "Flake is CI-only, not local", "confidence": "medium"}],
    "artifacts": [],
}

AGYLOOP_TURN = {
    "complete": True,
    "remaining_work": [],
    "summary": "Added web search citation for the API doc link.",
    "questions": [],
    "decisions": [],
    "assumptions": [],
    "artifacts": [{"kind": "report", "path": "research/citations.md"}],
}


def test_claudeloop_style_turn_extracts_cleanly() -> None:
    result = extract_events(CLAUDELOOP_TURN, open_items=(), now=NOW)
    assert len(result.events) == 5


def test_codexloop_style_turn_extracts_cleanly() -> None:
    result = extract_events(CODEXLOOP_TURN, open_items=(), now=NOW)
    kinds = [e.kind for e in result.events]
    assert kinds == ["DecisionRecorded", "ArtifactProduced", "VerdictRendered"]


def test_cursorloop_style_turn_extracts_cleanly() -> None:
    result = extract_events(CURSORLOOP_TURN, open_items=(), now=NOW)
    kinds = [e.kind for e in result.events]
    assert kinds == ["QuestionAsked", "AssumptionStated", "VerdictRendered"]


def test_agyloop_style_turn_extracts_cleanly() -> None:
    result = extract_events(AGYLOOP_TURN, open_items=(), now=NOW)
    kinds = [e.kind for e in result.events]
    assert kinds == ["ArtifactProduced", "VerdictRendered"]


def test_an_already_open_decision_is_reused_rather_than_minted_again() -> None:
    """Re-minting on every turn would fill the ledger with duplicates of the
    same decision and leave the handoff gate unable to tell what is still open."""
    title = "outbox over two-phase commit"
    existing = OpenItemRef(
        item_id="dec-existing",
        kind=OpenItemKind.DECISION,
        normalized=normalize_text(title),
    )

    result = extract_events(
        {"complete": False, "decisions": [{"title": title, "rationale": "simpler"}]},
        now=NOW,
        open_items=[existing],
    )

    assert result.reused_ids[title] == "dec-existing"
    assert not [e for e in result.events if str(e.kind).startswith("Decision")]


def test_an_already_open_assumption_is_reused_rather_than_minted_again() -> None:
    text = "postgres is the only write database"
    existing = OpenItemRef(
        item_id="asm-existing",
        kind=OpenItemKind.ASSUMPTION,
        normalized=normalize_text(text),
    )

    result = extract_events(
        {"complete": False, "assumptions": [{"text": text, "confidence": "high"}]},
        now=NOW,
        open_items=[existing],
    )

    assert result.reused_ids[text] == "asm-existing"
