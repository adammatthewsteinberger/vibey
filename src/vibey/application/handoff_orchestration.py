# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Gate escalation: STRICT (up to 3 attempts, regenerating with the
specific violations fed back) -> FULL_TRANSCRIPT (one attempt, the whole
range inlined) -> HUMAN (the job parks). handoff-protocol.md §6.4."""

from collections.abc import Sequence
from dataclasses import dataclass, replace

from vibey.application.ports import BriefProducer
from vibey.domain.handoff import (
    BudgetSnapshot,
    GateMode,
    GateResult,
    HandoffBrief,
    LedgerRef,
    Violation,
)
from vibey.domain.ledger import LedgerEvent
from vibey.domain.noloss import verify

MAX_STRICT_ATTEMPTS = 3


@dataclass(frozen=True, slots=True)
class HandoffOutcome:
    result: GateResult
    brief: HandoffBrief


async def produce_and_verify_handoff(
    *,
    producer: BriefProducer,
    ledger: Sequence[LedgerEvent],
    ref: LedgerRef,
    budget: BudgetSnapshot,
    spec_constraints: Sequence[str] = (),
) -> HandoffOutcome:
    attempt = 1
    mode = GateMode.STRICT
    violations: tuple[Violation, ...] = ()

    while True:
        brief = await producer.produce(attempt=attempt, mode=mode, violations=violations)
        result = verify(
            ledger=ledger,
            brief=brief,
            ref=ref,
            budget=budget,
            spec_constraints=spec_constraints,
            mode=mode,
            attempts=attempt,
        )

        if result.ok:
            return HandoffOutcome(result=result, brief=brief)

        if mode is GateMode.STRICT and attempt < MAX_STRICT_ATTEMPTS:
            attempt += 1
            violations = result.violations
            continue

        if mode is GateMode.STRICT:
            # Exhausted STRICT attempts: one shot at FULL_TRANSCRIPT, which
            # auto-satisfies the closure rules by inlining the whole range.
            mode = GateMode.FULL_TRANSCRIPT
            attempt += 1
            violations = result.violations
            continue

        # FULL_TRANSCRIPT itself failed (R6/R8/R10 only) -- park on a human
        # gate rather than proceed on a failed gate.
        return HandoffOutcome(result=replace(result, mode=GateMode.HUMAN), brief=brief)
