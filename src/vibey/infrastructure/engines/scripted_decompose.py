# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Deterministic WorkPlanProducer: the faked half of the two-mode harness.

Emits the walking skeleton first (no dependencies, per phase-protocols.md
2.1's "goes first, alone" rule) and one work item per acceptance criterion,
each depending only on the skeleton -- trivially topologically valid, and
every criterion maps to exactly one item, so `validate_decomposition` passes
by construction for any buildable spec. The live, model-driven producer
lands with rotation wiring; this one powers `--provider scripted` and CI.
"""

from vibey.domain.effort import Effort
from vibey.domain.plan import VerificationSpec, WorkItem
from vibey.domain.spec import DesignSpec

WALKING_SKELETON_ITEM_ID = "ws"


class ScriptedWorkPlanProducer:
    async def decompose(self, spec: DesignSpec) -> tuple[WorkItem, ...]:
        # build.verify refuses any item whose verification checks no
        # criteria (an item that names nothing can never be verified), so
        # the skeleton checks the first criterion -- the walking skeleton
        # proves the primary path end to end.
        skeleton_checks = (spec.criteria[0].criterion_id,) if spec.criteria else ()
        items = [
            WorkItem(
                item_id=WALKING_SKELETON_ITEM_ID,
                title=f"Walking skeleton: {spec.walking_skeleton}",
                acceptance_ids=(),
                depends_on=(),
                est_effort=Effort.STANDARD,
                files_touched_hint=(),
                verification=VerificationSpec(commands=(), criteria_checked=skeleton_checks),
            )
        ]
        for index, criterion in enumerate(spec.criteria, start=1):
            items.append(
                WorkItem(
                    item_id=f"item-{index:03d}",
                    title=f"Satisfy {criterion.criterion_id}: {criterion.then}",
                    acceptance_ids=(criterion.criterion_id,),
                    depends_on=(WALKING_SKELETON_ITEM_ID,),
                    est_effort=Effort.LOW,
                    files_touched_hint=(),
                    verification=VerificationSpec(
                        commands=(), criteria_checked=(criterion.criterion_id,)
                    ),
                )
            )
        return tuple(items)
