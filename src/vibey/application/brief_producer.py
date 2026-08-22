# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""The production default BriefProducer: vibey's own deterministic
template (handoff-protocol.md §6.5, option 4 -- "the floor"), promoted
from the forced-rotation test's `_DeterministicFloorProducer`. Built
directly from the same projections the no-loss gate checks, so it passes
the gate by construction; a wind-down's StopSummary.remaining_work is
merged in on top because the outgoing engine's final snapshot may know
about remaining work no ledger verdict recorded yet (R1 only checks
ledger -> brief coverage, so extra brief items are always safe).
"""

from dataclasses import dataclass, replace

from vibey.domain.briefing import build_deterministic_brief
from vibey.domain.handoff import GateMode, HandoffBrief, RemainingItem, Violation
from vibey.domain.ledger import LedgerEvent


@dataclass(frozen=True, slots=True)
class DeterministicBriefProducer:
    events: tuple[LedgerEvent, ...]
    objective: str = "See the accepted spec in .vibey/context/spec.md."
    spec_constraints: tuple[str, ...] = ()
    invariants: tuple[str, ...] = ()
    style_rules: tuple[str, ...] = ()
    extra_remaining: tuple[str, ...] = ()

    async def produce(
        self, *, attempt: int, mode: GateMode, violations: tuple[Violation, ...]
    ) -> HandoffBrief:
        # Deterministic by design: attempt/mode/violations are the
        # regeneration channel for model-written briefs; the floor has
        # nothing to regenerate differently.
        brief = build_deterministic_brief(
            self.events,
            objective=self.objective,
            spec_constraints=self.spec_constraints,
            invariants=self.invariants,
            style_rules=self.style_rules,
        )
        known = {item.text for item in brief.remaining}
        extra = tuple(
            RemainingItem(text=text) for text in self.extra_remaining if text not in known
        )
        if not extra:
            return brief
        remaining = brief.remaining + extra
        return replace(brief, remaining=remaining, next_action=remaining[0].text)
