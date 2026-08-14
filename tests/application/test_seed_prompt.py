from vibey.application.seed_prompt import closable_ids_in_brief, render_seed_prompt
from vibey.domain.handoff import AssumptionRef, DecisionRef, HandoffBrief, QuestionRef
from vibey.domain.review import Ambiguity, FindingRef, Severity


def _brief(**overrides: object) -> HandoffBrief:
    defaults: dict[str, object] = {
        "objective": "ship the outbox relay",
        "constraints": ("must work offline",),
        "decisions": (DecisionRef("d1", "outbox over 2PC"),),
        "assumptions": (AssumptionRef("a1", "postgres is the only write db"),),
        "done": ("migration 007 applied",),
        "remaining": (),
        "open_questions": (QuestionRef("q1", "capped or unbounded?", blocking=True),),
        "open_findings": (FindingRef("f1", Severity.HIGH, Ambiguity.CLEAR),),
        "artifacts": (),
        "invariants": ("all tests green",),
        "style_rules": ("use ruff format",),
        "next_action": "implement the retry cap",
    }
    defaults.update(overrides)
    return HandoffBrief(**defaults)  # type: ignore[arg-type]


def test_ledger_notice_is_always_present() -> None:
    prompt = render_seed_prompt(_brief())
    assert ".vibey/handoff/ledger.jsonl" in prompt
    assert "untrusted" in prompt


def test_every_closable_id_appears_verbatim_in_the_prompt() -> None:
    brief = _brief()
    prompt = render_seed_prompt(brief)

    for item_id in closable_ids_in_brief(brief):
        assert item_id in prompt


def test_objective_and_next_action_are_present() -> None:
    prompt = render_seed_prompt(_brief())
    assert "ship the outbox relay" in prompt
    assert "implement the retry cap" in prompt


def test_empty_sections_are_omitted() -> None:
    brief = _brief(
        constraints=(), decisions=(), assumptions=(), open_questions=(), open_findings=()
    )
    prompt = render_seed_prompt(brief)
    assert "Constraints:" not in prompt
    assert "Decisions already made" not in prompt
    assert "Open questions" not in prompt


def test_closable_ids_in_brief_covers_all_four_kinds() -> None:
    brief = _brief()
    ids = closable_ids_in_brief(brief)
    assert ids == {"d1", "a1", "q1", "f1"}
