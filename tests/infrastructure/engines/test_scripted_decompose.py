# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""ScriptedWorkPlanProducer: deterministic, structurally valid by construction."""

from vibey.domain.effort import Effort
from vibey.domain.plan import validate_decomposition
from vibey.domain.spec import AcceptanceCriterion, DesignSpec
from vibey.infrastructure.engines.scripted_decompose import (
    WALKING_SKELETON_ITEM_ID,
    ScriptedWorkPlanProducer,
)


def _spec(criteria_count: int = 2) -> DesignSpec:
    return DesignSpec(
        objective="a trivial greeter",
        constraints=(),
        non_goals=(),
        criteria=tuple(
            AcceptanceCriterion(
                criterion_id=f"ac-{i}",
                given="a name",
                when="greet is called",
                then=f"a greeting {i} is returned",
                fit="exact string match",
            )
            for i in range(1, criteria_count + 1)
        ),
        nfrs=(),
        walking_skeleton="greet() returns a constant string end to end",
    )


async def test_walking_skeleton_goes_first_alone() -> None:
    items = await ScriptedWorkPlanProducer().decompose(_spec())

    assert items[0].item_id == WALKING_SKELETON_ITEM_ID
    assert items[0].depends_on == ()
    assert items[0].est_effort is Effort.STANDARD


async def test_every_criterion_maps_to_exactly_one_item() -> None:
    spec = _spec(criteria_count=3)

    items = await ScriptedWorkPlanProducer().decompose(spec)

    assert len(items) == 4
    mapped = [item.acceptance_ids for item in items[1:]]
    assert mapped == [("ac-1",), ("ac-2",), ("ac-3",)]
    assert all(item.depends_on == (WALKING_SKELETON_ITEM_ID,) for item in items[1:])


async def test_output_passes_validate_decomposition() -> None:
    spec = _spec(criteria_count=2)

    items = await ScriptedWorkPlanProducer().decompose(spec)

    violations = validate_decomposition(
        items,
        criteria_ids=[c.criterion_id for c in spec.criteria],
        walking_skeleton_item_id=items[0].item_id,
    )
    assert violations == ()


async def test_skeleton_checks_the_first_criterion() -> None:
    """build.verify refuses items with empty criteria_checked -- the
    skeleton proves the primary path, so it checks the first criterion."""
    items = await ScriptedWorkPlanProducer().decompose(_spec())

    assert items[0].verification.criteria_checked == ("ac-1",)


async def test_spec_without_criteria_yields_a_bare_skeleton() -> None:
    items = await ScriptedWorkPlanProducer().decompose(_spec(criteria_count=0))

    assert len(items) == 1
    assert items[0].verification.criteria_checked == ()
