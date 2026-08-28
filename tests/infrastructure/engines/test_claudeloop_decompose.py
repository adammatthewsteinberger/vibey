# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""ClaudeLoopWorkPlanProducer: strict-JSON decoding and fail-fast validation."""

import json
from pathlib import Path

import pytest

from vibey.domain.effort import Effort
from vibey.domain.spec import AcceptanceCriterion, DesignSpec
from vibey.infrastructure.engines.claudeloop_decompose import ClaudeLoopWorkPlanProducer
from vibey.infrastructure.engines.claudeloop_process import ClaudeLoopResult


class FakeProcess:
    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.calls = []  # type: ignore[var-annotated]

    async def run(self, spec, *, web_search=False):  # type: ignore[no-untyped-def]
        self.calls.append((spec, web_search))
        return ClaudeLoopResult(
            "run-1",
            spec.worktree_path / ".claudeloop/runs/run-1",
            self.responses.pop(0),
        )


def _spec() -> DesignSpec:
    return DesignSpec(
        objective="a greeter",
        constraints=(),
        non_goals=(),
        criteria=(
            AcceptanceCriterion(
                criterion_id="AC-1",
                given="a name",
                when="greet runs",
                then="a greeting returns",
                fit="exact match",
            ),
        ),
        nfrs=(),
        walking_skeleton="greet() end to end",
    )


def _valid_items() -> str:
    return json.dumps(
        {
            "items": [
                {
                    "item_id": "ws",
                    "title": "walking skeleton",
                    "acceptance_ids": ["AC-1"],
                    "depends_on": [],
                    "est_effort": "standard",
                    "verification": {"commands": ["pytest -q"], "criteria_checked": ["AC-1"]},
                },
                {
                    "item_id": "item-1",
                    "title": "full greeting",
                    "acceptance_ids": ["AC-1"],
                    "depends_on": ["ws"],
                    "est_effort": "low",
                    "verification": {"commands": [], "criteria_checked": ["AC-1"]},
                },
            ]
        }
    )


async def test_decompose_decodes_a_valid_item_graph(tmp_path: Path) -> None:
    producer = ClaudeLoopWorkPlanProducer(
        process=FakeProcess([_valid_items()]), worktree_path=tmp_path
    )

    items = await producer.decompose(_spec())

    assert [item.item_id for item in items] == ["ws", "item-1"]
    assert items[0].depends_on == ()
    assert items[0].est_effort is Effort.STANDARD
    assert items[1].depends_on == ("ws",)
    assert items[1].verification.criteria_checked == ("AC-1",)


async def test_decompose_rejects_missing_or_empty_items(tmp_path: Path) -> None:
    for payload in ('{"items": []}', '{"nope": 1}'):
        producer = ClaudeLoopWorkPlanProducer(
            process=FakeProcess([payload]), worktree_path=tmp_path
        )
        with pytest.raises(ValueError, match="non-empty items list"):
            await producer.decompose(_spec())


async def test_decompose_rejects_non_object_items_and_missing_keys(tmp_path: Path) -> None:
    producer = ClaudeLoopWorkPlanProducer(
        process=FakeProcess(['{"items": ["not-an-object"]}']), worktree_path=tmp_path
    )
    with pytest.raises(ValueError, match="must be an object"):
        await producer.decompose(_spec())

    missing_key = json.dumps({"items": [{"title": "no id"}]})
    producer = ClaudeLoopWorkPlanProducer(
        process=FakeProcess([missing_key]), worktree_path=tmp_path
    )
    with pytest.raises(ValueError, match="missing item_id"):
        await producer.decompose(_spec())


async def test_decompose_rejects_bad_verification_and_list_shapes(tmp_path: Path) -> None:
    bad_verification = json.dumps(
        {"items": [{"item_id": "ws", "title": "x", "verification": "nope"}]}
    )
    producer = ClaudeLoopWorkPlanProducer(
        process=FakeProcess([bad_verification]), worktree_path=tmp_path
    )
    with pytest.raises(ValueError, match="verification must be an object"):
        await producer.decompose(_spec())

    bad_list = json.dumps({"items": [{"item_id": "ws", "title": "x", "acceptance_ids": "AC-1"}]})
    producer = ClaudeLoopWorkPlanProducer(process=FakeProcess([bad_list]), worktree_path=tmp_path)
    with pytest.raises(ValueError, match="expected a list"):
        await producer.decompose(_spec())


async def test_decompose_fails_fast_on_a_structurally_invalid_graph(tmp_path: Path) -> None:
    """The model mapped no criteria and gave the skeleton a dependency --
    the producer names the violations instead of shipping them onward."""
    invalid = json.dumps(
        {
            "items": [
                {
                    "item_id": "ws",
                    "title": "skeleton",
                    "acceptance_ids": [],
                    "depends_on": ["item-1"],
                    "est_effort": "low",
                    "verification": {"commands": [], "criteria_checked": ["AC-1"]},
                },
                {
                    "item_id": "item-1",
                    "title": "thing",
                    "acceptance_ids": [],
                    "depends_on": [],
                    "est_effort": "low",
                    "verification": {"commands": [], "criteria_checked": ["AC-1"]},
                },
            ]
        }
    )
    producer = ClaudeLoopWorkPlanProducer(process=FakeProcess([invalid]), worktree_path=tmp_path)

    with pytest.raises(ValueError, match="invalid decomposition"):
        await producer.decompose(_spec())


async def test_decompose_normalizes_model_ids_to_the_worktree_shape(tmp_path: Path) -> None:
    """Caught live: the model returned "WI-01"-style ids and every
    implement attempt died on worktree-id validation, burning the ladder."""
    payload = json.dumps(
        {
            "items": [
                {
                    "item_id": "WS",
                    "title": "walking skeleton",
                    "acceptance_ids": ["AC-1"],
                    "depends_on": [],
                    "est_effort": "standard",
                    "verification": {"commands": [], "criteria_checked": ["AC-1"]},
                },
                {
                    "item_id": "WI_01: CLI parsing",
                    "title": "cli parsing",
                    "acceptance_ids": ["AC-1"],
                    "depends_on": ["WS"],
                    "est_effort": "low",
                    "verification": {"commands": [], "criteria_checked": ["AC-1"]},
                },
            ]
        }
    )
    producer = ClaudeLoopWorkPlanProducer(process=FakeProcess([payload]), worktree_path=tmp_path)

    items = await producer.decompose(_spec())

    assert [item.item_id for item in items] == ["ws", "wi-01-cli-parsing"]
    assert items[1].depends_on == ("ws",)


async def test_decompose_rejects_ids_that_collide_or_vanish_after_normalization(
    tmp_path: Path,
) -> None:
    colliding = json.dumps(
        {
            "items": [
                {
                    "item_id": "WS",
                    "title": "skeleton",
                    "acceptance_ids": ["AC-1"],
                    "depends_on": [],
                    "est_effort": "low",
                    "verification": {"commands": [], "criteria_checked": ["AC-1"]},
                },
                {
                    "item_id": "ws",
                    "title": "duplicate",
                    "acceptance_ids": ["AC-1"],
                    "depends_on": [],
                    "est_effort": "low",
                    "verification": {"commands": [], "criteria_checked": ["AC-1"]},
                },
            ]
        }
    )
    producer = ClaudeLoopWorkPlanProducer(process=FakeProcess([colliding]), worktree_path=tmp_path)
    with pytest.raises(ValueError, match="duplicate item id"):
        await producer.decompose(_spec())

    vanishing = json.dumps(
        {
            "items": [
                {
                    "item_id": "***",
                    "title": "nothing left",
                    "acceptance_ids": ["AC-1"],
                    "depends_on": [],
                    "est_effort": "low",
                    "verification": {"commands": [], "criteria_checked": ["AC-1"]},
                }
            ]
        }
    )
    producer = ClaudeLoopWorkPlanProducer(process=FakeProcess([vanishing]), worktree_path=tmp_path)
    with pytest.raises(ValueError, match="normalizes to nothing"):
        await producer.decompose(_spec())


async def test_decompose_prompt_carries_the_verification_house_rules(tmp_path: Path) -> None:
    """Engines invented per-item verification styles and root-level test
    stubs live; the prompt must pin the expectations."""
    process = FakeProcess([_valid_items()])
    producer = ClaudeLoopWorkPlanProducer(process=process, worktree_path=tmp_path)

    await producer.decompose(_spec())

    (call,) = process.calls
    prompt = call[0].prompt
    assert "self-contained" in prompt
    assert "clean checkout" in prompt
    assert "tests/" in prompt
    assert "chained via depends_on" in prompt
