# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""kopf handlers for the VibeyProject custom resource.

Deliberately thin. Every decision worth testing lives in
`application/operator_projection.py`, which is pure, and every write goes
through the same application services the CLI uses -- runbook 05 names the
alternative as a real risk: a custom resource growing its own copy of the
transition, enqueue, and answer logic, which then drifts from `vibey new`
and `vibey answer` without anyone noticing.

The CR is declarative and level-triggered, so every handler here must be
safe to run again on unchanged input. Creating a project is guarded by the
id recorded in `status`; enqueueing the interview is guarded by the job's
idempotency key; answering is guarded by the gate no longer being open.
"""

from collections.abc import Mapping
from pathlib import Path
from typing import Any
from uuid import UUID

import kopf

from vibey.application.dto import ProjectRecord
from vibey.application.operator_projection import AnswerPlan, plan_answers, project_status
from vibey.application.project_kickoff import enqueue_design_interview
from vibey.bootstrap import AppResources, build_app

GROUP = "vibey.dev"
VERSION = "v1alpha1"
PLURAL = "vibeyprojects"

# Long enough that the operator is not a hot loop against Postgres, short
# enough that a park reaches a human's dashboard while they still care.
RECONCILE_INTERVAL = 15.0

ANSWERED_BY = "operator"


def _project_config(name: str, spec: Mapping[str, Any]) -> dict[str, object]:
    config: dict[str, object] = {
        "project": {"name": name, "repo": str(spec.get("repo", "."))},
    }
    if spec.get("maxCycleDollars") is not None:
        config["max_cycle_dollars"] = spec["maxCycleDollars"]
    if spec.get("maxCycleTurns") is not None:
        config["max_cycle_turns"] = spec["maxCycleTurns"]
    if spec.get("engines"):
        config["engines"] = list(spec["engines"])
    if spec.get("skillsContext") is not None:
        context = spec["skillsContext"]
        if not isinstance(context, Mapping):
            raise ValueError("spec.skillsContext must be an object")
        config["skills_context"] = dict(context)
    return config


async def ensure_project(
    resources: AppResources,
    *,
    name: str,
    spec: Mapping[str, Any],
    known_project_id: str | None,
) -> ProjectRecord:
    """Return the project this CR refers to, creating it only once.

    `status.projectId` is the guard. Without it a re-created CR, or a
    reconcile that fired before the first status patch landed, would start a
    second project against the same repository.
    """
    if known_project_id is not None:
        existing = await resources.projects.get(UUID(known_project_id))
        if existing is not None:
            return existing

    project = await resources.projects.create(
        name,
        Path(str(spec.get("repo", "."))),
        max_cycles=int(spec.get("maxCycles", 10)),
        config=_project_config(name, spec),
    )
    await enqueue_design_interview(
        projects=resources.projects,
        jobs=resources.jobs,
        project_id=project.project_id,
        origin="operator",
    )
    return project


async def apply_answers(
    resources: AppResources,
    *,
    project_id: UUID,
    spec_answers: Mapping[str, object],
) -> AnswerPlan:
    """Apply `spec.answers` through the same service `vibey answer` uses."""
    open_gates = await resources.gates.open_for_project(project_id)
    plan = plan_answers(spec_answers, open_gates)
    for gate_id, payload in plan.apply:
        await resources.gates.answer(gate_id, answer=payload, answered_by=ANSWERED_BY)
    return plan


async def build_status(resources: AppResources, *, project_id: UUID) -> dict[str, object]:
    project = await resources.projects.get(project_id)
    if project is None:
        return {
            "projectId": str(project_id),
            "phase": "unknown",
            "conditions": [
                {
                    "type": "Ready",
                    "status": "Unknown",
                    "reason": "ProjectMissing",
                    "message": "status names a project that no longer exists",
                }
            ],
        }
    open_gates = await resources.gates.open_for_project(project_id)
    return project_status(project, open_gates)


@kopf.on.create(GROUP, VERSION, PLURAL)
async def on_create(
    spec: Mapping[str, Any],
    name: str | None,
    patch: kopf.Patch,
    **_: Any,
) -> None:
    async with build_app() as resources:
        project = await ensure_project(
            resources,
            name=str(name),
            spec=spec,
            known_project_id=None,
        )
        patch.status.update(await build_status(resources, project_id=project.project_id))


@kopf.timer(GROUP, VERSION, PLURAL, interval=RECONCILE_INTERVAL)
async def reconcile(
    spec: Mapping[str, Any],
    status: Mapping[str, Any],
    name: str | None,
    patch: kopf.Patch,
    **_: Any,
) -> None:
    """Level-triggered: recompute from observed state every interval rather
    than reacting to events, so a missed event or a restarted operator
    changes nothing about the outcome."""
    async with build_app() as resources:
        project = await ensure_project(
            resources,
            name=str(name),
            spec=spec,
            known_project_id=status.get("projectId"),
        )
        answers = spec.get("answers") or {}
        plan = await apply_answers(
            resources,
            project_id=project.project_id,
            spec_answers=answers,
        )
        new_status = await build_status(resources, project_id=project.project_id)
        if plan.ignored:
            new_status["ignoredAnswers"] = [
                {"key": key, "reason": reason} for key, reason in plan.ignored
            ]
        patch.status.update(new_status)


def run(*, namespace: str | None = None) -> None:
    """Block running the kopf event loop. Separated so the handlers above
    stay importable and testable without starting an operator.

    No coverage pragma here on purpose: a one-line delegation is exactly
    the kind of thing that gets a suppression instead of a test, and
    runbook 18 counts those.
    """
    kopf.run(namespace=namespace, clusterwide=namespace is None)
