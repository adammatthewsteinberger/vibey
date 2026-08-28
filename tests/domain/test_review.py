# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
from datetime import UTC, datetime
from uuid import uuid4

from vibey.domain.engine import EngineId
from vibey.domain.ledger import EventKind, LedgerEvent, Provenance
from vibey.domain.phase import Phase
from vibey.domain.projections import build_deltas
from vibey.domain.review import (
    Ambiguity,
    DeltasReport,
    FindingRef,
    Severity,
    UserVerdict,
    render_deltas_markdown,
    render_demo_markdown,
    render_run_it_script,
    render_walkthrough_markdown,
)
from vibey.domain.spec import AcceptanceCriterion, DesignSpec

NOW = datetime(2026, 8, 15, tzinfo=UTC)


def _make_event(
    kind: EventKind,
    payload: dict[str, object],
    *,
    seq: int = 1,
    phase: Phase = Phase.BUILD,
) -> LedgerEvent:
    return LedgerEvent(
        event_id=uuid4(),
        project_id=uuid4(),
        cycle=1,
        phase=phase,
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


def test_review_domain_types() -> None:
    assert Severity.CRITICAL.value == "critical"
    assert Severity.HIGH.value == "high"
    assert Severity.MEDIUM.value == "medium"
    assert Severity.LOW.value == "low"

    assert Ambiguity.CLEAR.value == "clear"
    assert Ambiguity.NEEDS_CLARIFICATION.value == "needs_clarification"

    assert UserVerdict.ACCEPT.value == "accept"
    assert UserVerdict.CHANGES.value == "changes"
    assert UserVerdict.CANCEL.value == "cancel"

    ref = FindingRef("f1", Severity.HIGH, Ambiguity.CLEAR)
    assert ref.finding_id == "f1"
    assert ref.severity == Severity.HIGH
    assert ref.ambiguity == Ambiguity.CLEAR


def test_build_deltas_empty_events() -> None:
    deltas = build_deltas(())
    assert isinstance(deltas, DeltasReport)
    assert len(deltas.assumptions) == 0
    assert len(deltas.findings) == 0

    md = render_deltas_markdown(deltas)
    assert "No assumptions recorded." in md
    assert "No findings recorded." in md


def test_build_deltas_extracts_assumptions_and_findings() -> None:
    events = (
        _make_event(
            EventKind.ASSUMPTION_STATED,
            {"assumption_id": "a-1", "text": "Assume offline-first storage."},
            seq=1,
            phase=Phase.DESIGN,
        ),
        _make_event(
            EventKind.FINDING_RAISED,
            {
                "finding_id": "f-101",
                "severity": "high",
                "ambiguity": "clear",
                "text": "Header spelling error.",
            },
            seq=2,
            phase=Phase.BUILD,
        ),
        _make_event(
            EventKind.FINDING_RAISED,
            {
                "finding_id": "f-102",
                "severity": "unknown_sev",
                "ambiguity": "unknown_amb",
                "text": "Ambiguous edge case.",
            },
            seq=3,
            phase=Phase.BUILD,
        ),
        _make_event(
            EventKind.FINDING_RESOLVED,
            {"finding_id": "f-101"},
            seq=4,
            phase=Phase.BUILD,
        ),
    )

    deltas = build_deltas(events)
    assert len(deltas.assumptions) == 1
    assert deltas.assumptions[0].assumption_id == "a-1"
    assert deltas.assumptions[0].text == "Assume offline-first storage."
    assert deltas.assumptions[0].seq == 1

    assert len(deltas.findings) == 2
    f1 = next(f for f in deltas.findings if f.finding_id == "f-101")
    assert f1.severity == Severity.HIGH
    assert f1.ambiguity == Ambiguity.CLEAR
    assert f1.resolved is True

    f2 = next(f for f in deltas.findings if f.finding_id == "f-102")
    assert f2.severity == Severity.LOW  # fallback
    assert f2.ambiguity == Ambiguity.NEEDS_CLARIFICATION  # fallback
    assert f2.resolved is False

    md = render_deltas_markdown(deltas)
    assert "a-1" in md
    assert "Assume offline-first storage." in md
    assert "f-101" in md
    assert "Header spelling error." in md
    assert "f-102" in md
    assert "Ambiguous edge case." in md
    assert "[RESOLVED]" in md


def test_render_demo_markdown() -> None:
    spec = DesignSpec(
        objective="Deliver notes app",
        constraints=(),
        non_goals=(),
        criteria=(
            AcceptanceCriterion(
                criterion_id="AC-1",
                given="a blank notebook",
                when="create note is clicked",
                then="a new note is opened",
                fit="created within 100ms",
            ),
        ),
        nfrs=(),
        walking_skeleton="walking skeleton",
    )
    md = render_demo_markdown(spec, evidence={"AC-1": "PASSED: test_create_note"})
    assert "# Demo: Deliver notes app" in md
    assert "AC-1" in md
    assert "PASSED: test_create_note" in md


def test_render_run_it_script() -> None:
    script = render_run_it_script(["pytest", "python -m myapp"])
    assert "#!/usr/bin/env bash" in script
    assert "set -euo pipefail" in script
    assert "pytest" in script
    assert "python -m myapp" in script

    default_script = render_run_it_script()
    assert "echo 'Run verification suite'" in default_script
    assert "pytest" in default_script


def test_render_walkthrough_markdown() -> None:
    spec = DesignSpec(
        objective="Deliver notes app",
        constraints=(),
        non_goals=(),
        criteria=(),
        nfrs=(),
        walking_skeleton="walking skeleton",
    )
    md = render_walkthrough_markdown(
        spec=spec,
        summary="Implemented local storage.",
        work_items=["item-1"],
    )
    assert "# Walkthrough" in md
    assert "Deliver notes app" in md
    assert "Implemented local storage." in md
    assert "item-1" in md

    default_md = render_walkthrough_markdown()
    assert "Delivered changes." in default_md
