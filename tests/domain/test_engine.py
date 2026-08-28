# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
import pytest

from vibey.domain.effort import Effort
from vibey.domain.engine import (
    Capability,
    EngineDescriptor,
    EngineId,
    EngineInvocation,
    IsolationLevel,
    JobRequirement,
)


def _descriptor(effort_projection: dict[Effort, EngineInvocation]) -> EngineDescriptor:
    return EngineDescriptor(
        engine_id=EngineId.CODEXLOOP,
        binary="codexloop",
        min_version="1.0.0",
        state_dir=".codexloop",
        done_marker="CODEXLOOP_TASK_FULLY_COMPLETE",
        auth_env=("OPENAI_API_KEY",),
        capabilities=frozenset({Capability.STRUCTURED_VERDICT}),
        effort_projection=effort_projection,
        session_verb="resume",
        isolation_flags={IsolationLevel.WORKTREE: ()},
        cost_per_mtok_in=1.0,
        cost_per_mtok_out=2.0,
        context_window=128_000,
    )


def test_invoke_returns_exact_projection_when_present() -> None:
    descriptor = _descriptor(
        {
            Effort.LOW: EngineInvocation(("--effort", "low"), achieved=Effort.LOW),
            Effort.HIGH: EngineInvocation(("--effort", "high"), achieved=Effort.HIGH),
        }
    )

    assert descriptor.invoke(Effort.LOW).achieved is Effort.LOW
    assert descriptor.invoke(Effort.HIGH).achieved is Effort.HIGH


def test_invoke_falls_back_to_highest_projection_at_or_below_requested() -> None:
    descriptor = _descriptor(
        {
            Effort.TRIVIAL: EngineInvocation((), achieved=Effort.TRIVIAL),
            Effort.HIGH: EngineInvocation(("--effort", "high"), achieved=Effort.HIGH),
        }
    )

    invocation = descriptor.invoke(Effort.MAX)

    assert invocation.achieved is Effort.HIGH


def test_invoke_raises_when_no_projection_at_or_below_requested() -> None:
    descriptor = _descriptor(
        {Effort.HIGH: EngineInvocation(("--effort", "high"), achieved=Effort.HIGH)}
    )

    with pytest.raises(KeyError):
        descriptor.invoke(Effort.LOW)


@pytest.mark.parametrize(
    ("requested", "achieved", "expected_saturated"),
    [
        (Effort.HIGH, Effort.HIGH, False),
        (Effort.MAX, Effort.HIGH, True),
        (Effort.LOW, Effort.LOW, False),
        (Effort.STANDARD, Effort.HIGH, False),
    ],
)
def test_saturates_at_truth_table(
    requested: Effort, achieved: Effort, expected_saturated: bool
) -> None:
    descriptor = _descriptor({requested: EngineInvocation((), achieved=achieved)})

    assert descriptor.saturates_at(requested) is expected_saturated


def test_job_requirement_defaults() -> None:
    requirement = JobRequirement(effort=Effort.STANDARD)

    assert requirement.capabilities == frozenset()
    assert requirement.excluded == frozenset()


def test_job_requirement_excluded_carries_the_must_differ_constraint() -> None:
    requirement = JobRequirement(effort=Effort.HIGH, excluded=frozenset({EngineId.CLAUDELOOP}))

    assert EngineId.CLAUDELOOP in requirement.excluded
