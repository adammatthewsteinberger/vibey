# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The fit calculus as a running control loop, with its reasoning kept (#263).

`fit` measures both sides and decides once. This closes the loop around it: every
completed operation feeds its own timing back, the constants are re-fitted from a
rolling window rather than assumed, and **every decision is written down with the
inputs that produced it** — so an admission can be explained months later instead of
being re-derived from a shrug.

Three properties are the point.

**Self-adjusting.** The window is bounded, so the estimate tracks what the machine is
doing *now*. A model that was swapped out, a machine that gained free memory, a run of
unusually large payloads — each moves τ and s within a few operations rather than
being averaged into irrelevance by history.

**Reconstructible.** The journal records the whole basis of each decision: the
projection, the constants, the queue, the payload, the deadline. Recording only the
verdict would leave "why was this deferred?" unanswerable, which is the state doctrine
7 exists to prevent.

**Bounded.** This loop does not resize swap, and that is deliberate rather than
unfinished. #263 asks for headroom to be scaled autonomously; growing paging space is
an irreversible act on somebody's machine, and the floor rule puts irreversible acts
in a human's hands. So the loop computes exactly what to change, says so loudly, and
stops there. `recommendation()` is the output; acting on it is the operator's.

At the floor — a model the machine cannot host at all — it stops adjusting and says
so in plain words, in under one service time, which is what doctrine 10's
clarification requires of it.
"""

from __future__ import annotations

import json
import time
from collections import deque
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path

from vibey_gh.fit import (
    FLOOR,
    Estimate,
    Fit,
    Machine,
    Model,
    Observation,
    decide,
    estimate_from,
    sample_machine,
    sample_model,
)

__all__ = ["Decision", "FitLoop", "recorded_observations"]

# `None` is a real answer for a model — "the runner does not hold it", which is the
# FLOOR case — so it cannot double as "the caller did not say". A caller that has
# already determined there is no model must be able to state that without the loop
# helpfully going and finding one.
_UNSET: object = object()


def recorded_observations(journal: Path) -> list[Observation]:
    """Measurements a previous run wrote, so constants carry across invocations.

    Only entries a caller recorded through `observe()` are returned — never a decision's
    *projection*. Feeding a projection back as a measurement would let the estimate
    confirm its own guesses and drift from the machine while growing more confident.

    A missing, unreadable, or partly corrupt journal yields what it can rather than
    raising: an admission controller that will not run because its own logbook is
    damaged has made observability a single point of failure.
    """
    try:
        lines = journal.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    samples: list[Observation] = []
    for line in lines:
        try:
            entry = json.loads(line)
            if entry.get("kind") != "observation":
                continue
            samples.append(
                Observation(
                    payload_bytes=int(entry["payload_bytes"]),
                    elapsed_s=float(entry["elapsed_s"]),
                    concurrent=int(entry["concurrent"]),
                )
            )
        except (json.JSONDecodeError, AttributeError, KeyError, TypeError, ValueError):
            continue
    return samples


# Enough to span several rungs of concurrency without letting an hour-old machine
# state govern the next admission.
DEFAULT_WINDOW = 64


@dataclass(frozen=True)
class Decision:
    """One admission, with everything needed to re-derive it."""

    at: float
    verdict: str
    reason: str
    payload_bytes: int
    deadline_s: float
    queue_depth: int
    slots: float
    base_s: float
    rate_s_per_kb: float
    samples: int
    projected_wait_s: float
    projected_service_s: float
    headroom_gb: float
    free_gb: float
    model: str
    notes: tuple[str, ...] = field(default=())


class FitLoop:
    """A continuously re-fitted admission controller for one model on one machine."""

    def __init__(
        self,
        model_name: str,
        *,
        journal: Path | None = None,
        window: int = DEFAULT_WINDOW,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self.model_name = model_name
        self.journal = journal
        self._observations: deque[Observation] = deque(maxlen=max(window, 1))
        self._clock = clock or time.time
        self._decisions: list[Decision] = []

    # -- measurement ------------------------------------------------------------

    def observe(self, payload_bytes: int, elapsed_s: float, concurrent: int) -> None:
        """Feed one completed operation back into the estimate.

        The calculus is computed for all operations, always — which only means anything
        if every operation reports what it actually cost.

        Journalled under its own `kind`, and read back only from there. A projection must
        never re-enter the loop as if it were a measurement: doing so would let the model
        confirm its own guesses, and the estimate would drift away from the machine while
        looking more confident with every cycle.
        """
        self._observations.append(
            Observation(payload_bytes=payload_bytes, elapsed_s=elapsed_s, concurrent=concurrent)
        )
        self._write(
            {
                "kind": "observation",
                "at": round(self._clock(), 3),
                "payload_bytes": payload_bytes,
                "elapsed_s": elapsed_s,
                "concurrent": concurrent,
                "model": self.model_name,
            }
        )

    @property
    def estimate(self) -> Estimate:
        return estimate_from(list(self._observations))

    @property
    def decisions(self) -> tuple[Decision, ...]:
        return tuple(self._decisions)

    # -- decision ---------------------------------------------------------------

    def admit(
        self,
        *,
        payload_bytes: int,
        deadline_s: float,
        queue_depth: int = 0,
        machine: Machine | None = None,
        model: Model | None | object = _UNSET,
    ) -> Fit:
        """Sample both sides, decide, and record the decision with its basis.

        The machine is re-sampled per call rather than cached: free memory moved by three
        points *within* a single stress rung, and an admission made against a stale
        reading is exactly the kind of confident wrong answer this module exists to avoid.
        """
        machine = sample_machine() if machine is None else machine
        if model is _UNSET:
            model = sample_model(self.model_name)
        resolved = model if isinstance(model, Model) else None
        est = self.estimate
        verdict = decide(
            machine,
            resolved,
            est,
            queue_depth=queue_depth,
            payload_bytes=payload_bytes,
            deadline_s=deadline_s,
        )
        self._record(verdict, est, machine, payload_bytes, deadline_s, queue_depth)
        return verdict

    def _record(
        self,
        verdict: Fit,
        est: Estimate,
        machine: Machine,
        payload_bytes: int,
        deadline_s: float,
        queue_depth: int,
    ) -> None:
        entry = Decision(
            at=round(self._clock(), 3),
            verdict=verdict.verdict,
            reason=verdict.reason,
            payload_bytes=payload_bytes,
            deadline_s=deadline_s,
            queue_depth=queue_depth,
            slots=est.slots,
            base_s=est.base_s,
            rate_s_per_kb=est.rate_s_per_kb,
            samples=est.samples,
            projected_wait_s=verdict.projected_wait_s,
            projected_service_s=verdict.projected_service_s,
            headroom_gb=verdict.headroom_gb,
            free_gb=machine.free_gb,
            model=self.model_name,
            notes=verdict.notes,
        )
        self._decisions.append(entry)
        self._write({"kind": "decision", **asdict(entry)})

    def _write(self, payload: dict) -> None:
        if self.journal is None:
            return
        try:
            self.journal.parent.mkdir(parents=True, exist_ok=True)
            with self.journal.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, sort_keys=True) + "\n")
        except OSError:
            # A journal that cannot be written must never take the admission down with
            # it. Losing the record is bad; refusing the work because of it is worse.
            pass

    # -- what the human is asked to do ------------------------------------------

    def recommendation(self) -> str | None:
        """The loudest thing the loop currently wants a human to know, or None.

        The floor outranks headroom: a machine that cannot host the model at all is not
        helped by being told to grow its paging space.
        """
        if not self._decisions:
            return None
        last = self._decisions[-1]
        if last.verdict == FLOOR:
            return f"FLOOR — {last.reason}"
        if last.headroom_gb > 0:
            return (
                f"grow paging space by at least {last.headroom_gb} GB before it is needed:"
                f" the projection for {self.model_name} wants more headroom than the"
                f" {last.free_gb} GB free at the last sample. This loop will not resize"
                " swap by itself — an irreversible change to your machine is yours to make"
            )
        return None
