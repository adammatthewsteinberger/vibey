# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
from dataclasses import dataclass
from enum import StrEnum


class ConstraintKind(StrEnum):
    HARD = "hard"
    SOFT = "soft"


@dataclass(frozen=True, slots=True)
class Constraint:
    text: str
    kind: ConstraintKind


@dataclass(frozen=True, slots=True)
class AcceptanceCriterion:
    criterion_id: str
    given: str
    when: str
    then: str
    fit: str


@dataclass(frozen=True, slots=True)
class NonFunctionalRequirement:
    """Planguage. 'fast' is not an NFR; a scale and a meter are."""

    nfr_id: str
    attribute: str
    scale: str
    meter: str
    must: str
    wish: str | None
    fit_criterion: str


@dataclass(frozen=True, slots=True)
class DesignSpec:
    objective: str
    constraints: tuple[Constraint, ...]
    non_goals: tuple[str, ...]
    criteria: tuple[AcceptanceCriterion, ...]
    nfrs: tuple[NonFunctionalRequirement, ...]
    walking_skeleton: str

    def is_buildable(self) -> tuple[str, ...]:
        """Returns violations; empty means the DESIGN -> BUILD guard can pass."""
        violations = []
        if not self.criteria:
            violations.append("at least one acceptance criterion is required")
        if not self.walking_skeleton:
            violations.append("a walking skeleton must be identified")
        for criterion in self.criteria:
            if not criterion.fit:
                violations.append(
                    f"acceptance criterion {criterion.criterion_id!r} is missing a fit criterion"
                )
        for nfr in self.nfrs:
            if not nfr.scale or not nfr.meter or not nfr.must:
                violations.append(f"NFR {nfr.nfr_id!r} is missing a scale, meter, or must value")
        return tuple(violations)

    def hard_constraints(self) -> tuple[str, ...]:
        return tuple(c.text for c in self.constraints if c.kind is ConstraintKind.HARD)
