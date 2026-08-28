# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
from dataclasses import replace
from datetime import timedelta
from uuid import uuid4

from tests.application.fakes import FakeJobRepository, make_job
from vibey.application.build_decompose_handler import BuildDecomposeHandler
from vibey.application.worker import Failure, Success
from vibey.domain.effort import Effort
from vibey.domain.job import FailureClass
from vibey.domain.plan import VerificationSpec, WorkItem
from vibey.domain.spec import AcceptanceCriterion, DesignSpec


def spec() -> DesignSpec:
    return DesignSpec(
        "Ship",
        (),
        (),
        (
            AcceptanceCriterion("AC-1", "given", "when", "then", "fit"),
            AcceptanceCriterion("AC-2", "given", "when", "then", "fit"),
        ),
        (),
        "one path",
    )


def _item(item_id: str, **overrides: object) -> WorkItem:
    defaults: dict[str, object] = {
        "item_id": item_id,
        "title": f"do {item_id}",
        "acceptance_ids": (),
        "depends_on": (),
        "est_effort": Effort.LOW,
        "files_touched_hint": (),
        "verification": VerificationSpec(commands=("pytest",), criteria_checked=()),
    }
    defaults.update(overrides)
    return WorkItem(**defaults)  # type: ignore[arg-type]


class Specs:
    def __init__(self, value: DesignSpec | None) -> None:
        self.value = value

    async def load(self, project_id, cycle):  # type: ignore[no-untyped-def]
        return self.value


class Decomposer:
    def __init__(self, items: tuple[WorkItem, ...]) -> None:
        self.items = items

    async def decompose(self, spec):  # type: ignore[no-untyped-def]
        return self.items


async def test_decompose_fans_out_build_implement_jobs_in_dependency_order() -> None:
    job = replace(make_job(uuid4()), kind="build.decompose")
    items = (
        _item("skeleton", acceptance_ids=("AC-1",)),
        _item("item-2", acceptance_ids=("AC-2",), depends_on=("skeleton",)),
    )
    jobs = FakeJobRepository()
    handler = BuildDecomposeHandler(specs=Specs(spec()), decomposer=Decomposer(items), jobs=jobs)

    outcome = await handler.handle(job)

    assert isinstance(outcome, Success)
    skeleton_job = await jobs.claim(job.project_id, owner="w", lease=timedelta(seconds=5))
    assert skeleton_job is not None
    assert skeleton_job.work_item_id == "skeleton"
    assert skeleton_job.kind == "build.implement"
    await jobs.ack(skeleton_job.id, owner="w")
    item_2_job = await jobs.claim(job.project_id, owner="w", lease=timedelta(seconds=5))
    assert item_2_job is not None
    assert item_2_job.work_item_id == "item-2"


async def test_decompose_rejects_wrong_kind_and_missing_spec() -> None:
    handler = BuildDecomposeHandler(
        specs=Specs(None), decomposer=Decomposer(()), jobs=FakeJobRepository()
    )
    assert await handler.handle(make_job(uuid4())) == Failure(
        FailureClass.VIBEY, "expected build.decompose job"
    )
    job = replace(make_job(uuid4()), kind="build.decompose")
    outcome = await handler.handle(job)
    assert outcome == Failure(FailureClass.WORK, "no accepted design spec exists")


async def test_decompose_rejects_empty_and_unmapped_decompositions() -> None:
    job = replace(make_job(uuid4()), kind="build.decompose")

    empty = BuildDecomposeHandler(
        specs=Specs(spec()), decomposer=Decomposer(()), jobs=FakeJobRepository()
    )
    assert await empty.handle(job) == Failure(
        FailureClass.WORK, "decomposition produced no work items"
    )

    unmapped_items = (_item("skeleton", acceptance_ids=("AC-1",)),)
    unmapped = BuildDecomposeHandler(
        specs=Specs(spec()), decomposer=Decomposer(unmapped_items), jobs=FakeJobRepository()
    )
    outcome = await unmapped.handle(job)
    assert isinstance(outcome, Failure)
    assert outcome.failure_class is FailureClass.WORK
    assert "AC-2" in outcome.detail


async def test_decompose_rejects_a_topologically_invalid_item_order() -> None:
    job = replace(make_job(uuid4()), kind="build.decompose")
    items = (
        _item("skeleton", acceptance_ids=("AC-1",)),
        _item("item-2", acceptance_ids=("AC-2",), depends_on=("item-3",)),
        _item("item-3", acceptance_ids=()),
    )
    handler = BuildDecomposeHandler(
        specs=Specs(spec()), decomposer=Decomposer(items), jobs=FakeJobRepository()
    )
    outcome = await handler.handle(job)
    assert isinstance(outcome, Failure)
    assert outcome.failure_class is FailureClass.VIBEY
    assert "topologically" in outcome.detail


async def test_build_plan_kind_is_the_fast_loopback_spelling() -> None:
    """review.triage's fast loop-back enqueues 'build.plan'; the decompose
    handler accepts it as the same work."""
    job = replace(make_job(uuid4()), kind="build.plan")
    items = (_item("skeleton", acceptance_ids=("AC-1", "AC-2")),)
    jobs = FakeJobRepository()
    handler = BuildDecomposeHandler(specs=Specs(spec()), decomposer=Decomposer(items), jobs=jobs)

    outcome = await handler.handle(job)

    assert isinstance(outcome, Success)
    assert any(j.kind == "build.implement" for j in jobs._jobs.values())


async def test_fan_out_stamps_the_integration_base_ref_on_every_item() -> None:
    """Item branches stack on integrated code when any exists -- every
    item branching from the empty base rewrote the same module in
    parallel and guaranteed add/add merge conflicts, live."""
    from vibey.domain.worktree import branch_name

    job = replace(make_job(uuid4()), kind="build.decompose")
    items = (
        _item("skeleton", acceptance_ids=("AC-1",)),
        _item("item-2", acceptance_ids=("AC-2",), depends_on=("skeleton",)),
    )
    jobs = FakeJobRepository()
    handler = BuildDecomposeHandler(specs=Specs(spec()), decomposer=Decomposer(items), jobs=jobs)

    outcome = await handler.handle(job)

    assert isinstance(outcome, Success)
    records = list(jobs._jobs.values())
    assert len(records) == 2
    for record in records:
        assert record.payload["base_ref"] == branch_name(record.cycle, "integration")
