# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Projection from vibey's own state onto Kubernetes status conditions.

Pure by design: no kopf, no Kubernetes client, no I/O. The operator is
thin glue around this module, so the decisions that actually matter --
when a project is Ready, when it is Parked, which answers may be applied
-- are testable without a cluster.

Condition vocabulary follows Kubernetes' own convention rather than
inventing one: `status` is "True"/"False"/"Unknown" for the condition's
*type*, `reason` is a CamelCase token a machine can branch on, and
`message` is the part a human reads. Anyone who can read a Deployment's
conditions can read these.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from uuid import UUID

from vibey.application.dto import HumanGateRecord, ProjectRecord
from vibey.domain.phase import Phase

# Kubernetes truncates and humans skim. A park prompt can be a full
# interview; the CR carries a readable summary and the prompt itself stays
# in the ledger where it is not competing for space with etcd.
MAX_MESSAGE = 512

CONDITION_READY = "Ready"
CONDITION_PARKED = "Parked"
CONDITION_COMPLETE = "Complete"

TRUE = "True"
FALSE = "False"


@dataclass(frozen=True, slots=True)
class Condition:
    type: str
    status: str
    reason: str
    message: str


@dataclass(frozen=True, slots=True)
class AnswerPlan:
    """What the operator may apply from `spec.answers`, and what it may not.

    Rejections are returned rather than dropped: the CR is a second write
    path into gates, and a second write path that silently ignores input
    is how an operator appears to work while doing nothing.
    """

    apply: tuple[tuple[UUID, Mapping[str, object]], ...]
    ignored: tuple[tuple[str, str], ...]


def _truncate(text: str) -> str:
    collapsed = " ".join(text.split())
    if len(collapsed) <= MAX_MESSAGE:
        return collapsed
    return collapsed[: MAX_MESSAGE - 1] + "…"


def reason_for_kind(kind: str) -> str:
    """`budget_exhausted` -> `BudgetExhausted`.

    Kubernetes reasons are CamelCase alphanumeric tokens; a raw gate kind
    with underscores is not one, and tooling that filters on reason would
    silently miss it.
    """
    parts = [p for p in kind.replace("-", "_").split("_") if p.isalnum()]
    if not parts:
        return "Unknown"
    return "".join(p[:1].upper() + p[1:] for p in parts)


def project_conditions(
    project: ProjectRecord,
    open_gates: Sequence[HumanGateRecord],
) -> tuple[Condition, ...]:
    """The three conditions that answer an operator's actual questions:
    is it finished, is it stuck on me, and is it otherwise progressing."""
    complete = project.phase is Phase.DONE
    abandoned = project.phase is Phase.ABANDONED
    parked = len(open_gates) > 0

    if parked:
        first = open_gates[0]
        extra = f" (+{len(open_gates) - 1} more)" if len(open_gates) > 1 else ""
        park = Condition(
            CONDITION_PARKED,
            TRUE,
            reason_for_kind(first.kind),
            _truncate(f"{first.prompt}{extra}"),
        )
    else:
        park = Condition(CONDITION_PARKED, FALSE, "NoOpenGates", "no gate is awaiting an answer")

    if complete:
        ready = Condition(CONDITION_READY, FALSE, "Complete", "project reached DONE")
    elif abandoned:
        ready = Condition(CONDITION_READY, FALSE, "Abandoned", "project was abandoned")
    elif parked:
        ready = Condition(
            CONDITION_READY,
            FALSE,
            "AwaitingHuman",
            f"{len(open_gates)} gate(s) awaiting an answer",
        )
    else:
        ready = Condition(
            CONDITION_READY,
            TRUE,
            "Progressing",
            f"phase {project.phase.value}, cycle {project.cycle}/{project.max_cycles}",
        )

    done = Condition(
        CONDITION_COMPLETE,
        TRUE if complete else FALSE,
        "Done" if complete else "InProgress",
        f"phase {project.phase.value}",
    )
    return (ready, park, done)


def project_status(
    project: ProjectRecord,
    open_gates: Sequence[HumanGateRecord],
) -> dict[str, object]:
    return {
        "projectId": str(project.project_id),
        "phase": project.phase.value,
        "cycle": project.cycle,
        "maxCycles": project.max_cycles,
        "openGates": [
            {"gateId": str(g.gate_id), "kind": g.kind, "prompt": _truncate(g.prompt)}
            for g in open_gates
        ],
        "conditions": [
            {"type": c.type, "status": c.status, "reason": c.reason, "message": c.message}
            for c in project_conditions(project, open_gates)
        ],
    }


def plan_answers(
    spec_answers: Mapping[str, object],
    open_gates: Sequence[HumanGateRecord],
) -> AnswerPlan:
    """Match `spec.answers` keys against gates that are actually open.

    Answering an already-answered gate is not an error worth escalating --
    a CR is declarative and will still name yesterday's gate tomorrow --
    but it is not an action either, so it is reported as ignored rather
    than attempted. That is what makes re-applying an unchanged CR a no-op.
    """
    by_id = {g.gate_id: g for g in open_gates}
    apply: list[tuple[UUID, Mapping[str, object]]] = []
    ignored: list[tuple[str, str]] = []

    for key, payload in spec_answers.items():
        try:
            gate_id = UUID(key)
        except ValueError:
            ignored.append((key, "not a gate id"))
            continue
        if not isinstance(payload, Mapping):
            ignored.append((key, "answer must be an object"))
            continue
        if gate_id not in by_id:
            ignored.append((key, "no open gate with that id"))
            continue
        apply.append((gate_id, payload))

    return AnswerPlan(apply=tuple(apply), ignored=tuple(ignored))
