# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Build and render the accepted DESIGN output without performing I/O."""

from collections.abc import Sequence

from vibey.application.design import DesignEvent
from vibey.domain.ledger import EventKind, LedgerEvent
from vibey.domain.phase import TransitionEvidence, VisualDecision
from vibey.domain.review import UserVerdict
from vibey.domain.spec import DesignSpec


def build_design_evidence(
    spec: DesignSpec,
    *,
    open_blocking_questions: int,
    accepted: bool,
    # Defaults to DECLINED (never OPTED_IN) because the visual-design interstitial
    # (tasks 5.7-5.13) isn't built yet -- there is nowhere for an opt-in to go.
    # Callers get a real visual choice once that stage exists; this is not "yes
    # by default," it is the only decision that's currently honest.
    visual_decision: VisualDecision = VisualDecision.DECLINED,
) -> TransitionEvidence:
    return TransitionEvidence(
        acceptance_criteria=len(spec.criteria),
        open_blocking_questions=open_blocking_questions,
        user_verdict=UserVerdict.ACCEPT if accepted else None,
        visual_decision=visual_decision,
    )


def count_open_blocking_questions(events: Sequence[DesignEvent | LedgerEvent]) -> int:
    answered = {
        str(event.payload["item_id"])
        for event in events
        if event.kind is EventKind.ANSWER_GIVEN and "item_id" in event.payload
    }
    blocking = {
        str(event.payload["item_id"])
        for event in events
        if event.kind is EventKind.QUESTION_ASKED
        and event.payload.get("blocking") is True
        and "item_id" in event.payload
    }
    return len(blocking - answered)


def render_design_artifacts(
    spec: DesignSpec,
    *,
    decisions: Sequence[str] = (),
    assumptions: Sequence[str] = (),
) -> dict[str, str]:
    violations = spec.is_buildable()
    if violations:
        raise ValueError("; ".join(violations))

    constraints = (
        "\n".join(
            f"- [{constraint.kind.value}] {constraint.text}" for constraint in spec.constraints
        )
        or "- None"
    )
    non_goals = "\n".join(f"- {item}" for item in spec.non_goals) or "- None"
    spec_md = (
        f"# Design spec\n\n## Objective\n\n{spec.objective}\n\n"
        f"## Constraints\n\n{constraints}\n\n## Non-goals\n\n{non_goals}\n\n"
        f"## Walking skeleton\n\n{spec.walking_skeleton}\n"
    )

    acceptance_md = (
        "# Acceptance criteria\n\n"
        + "\n\n".join(
            f"## {criterion.criterion_id}\n\n"
            f"Given {criterion.given}\n\nWhen {criterion.when}\n\nThen {criterion.then}\n\n"
            f"Fit criterion: {criterion.fit}"
            for criterion in spec.criteria
        )
        + "\n"
    )

    nfr_md = (
        "# Non-functional requirements\n\n"
        + "\n\n".join(
            f"## {nfr.nfr_id}: {nfr.attribute}\n\n"
            f"Scale: {nfr.scale}\n\nMeter: {nfr.meter}\n\nMust: {nfr.must}\n\n"
            f"Wish: {nfr.wish or 'None'}\n\nFit criterion: {nfr.fit_criterion}"
            for nfr in spec.nfrs
        )
        + "\n"
    )

    decisions_md = (
        "# Decisions\n\n"
        + ("\n".join(f"- {decision}" for decision in decisions) or "- None")
        + "\n"
    )
    open_items_md = (
        "# Open items and assumptions\n\n"
        + ("\n".join(f"- {assumption}" for assumption in assumptions) or "- None")
        + "\n"
    )

    return {
        "spec.md": spec_md,
        "acceptance.md": acceptance_md,
        "nfr.md": nfr_md,
        "decisions.md": decisions_md,
        "open-items.md": open_items_md,
    }
