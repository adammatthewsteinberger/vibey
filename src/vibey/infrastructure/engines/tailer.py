# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Run-directory tailer: events.jsonl -> vibey LedgerEvents.

The runner's own event vocabulary (EngineEvent.kind) is deliberately the
same string vocabulary as domain.ledger.EventKind's values -- every adapter
is expected to normalize into it before vibey ever sees a line, the same
way domain/capacity.py's ADT is "inherited from the *loop family, unchanged
in spirit." Translation is therefore a validated identity mapping, not a
lookup table that could silently drop an unrecognized kind.

What this module does *not* do: mint event_id/seq/digest. Those are
assigned by vibey at ledger-append time (handoff-protocol.md §2 design
principle 4 -- ids are minted by vibey, never the agent), which happens in
the application layer once a project_id/cycle/phase/job_id context is
available. This module produces the fully-formed draft up to that point.
"""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from vibey.application.dto import EngineEvent
from vibey.domain.engine import EngineId
from vibey.domain.errors import VibeyError
from vibey.domain.ledger import EventKind, Provenance, canonical_bytes, digest_event
from vibey.domain.phase import Phase


class UnknownEventKind(VibeyError):
    def __init__(self, kind: str) -> None:
        self.kind = kind
        super().__init__(f"engine emitted an event kind vibey does not recognize: {kind!r}")


@dataclass(frozen=True, slots=True)
class LedgerEventDraft:
    """Everything a LedgerEvent needs except event_id, seq, and the range
    the digest folds over -- those are minted by the ledger appender."""

    project_id: UUID
    cycle: int
    phase: Phase
    kind: EventKind
    engine_id: EngineId | None
    job_id: UUID | None
    causation_id: UUID | None
    correlation_id: UUID
    provenance: Provenance
    produced_at: datetime
    payload: dict[str, object]
    digest: str


def translate_event(
    event: EngineEvent,
    *,
    project_id: UUID,
    cycle: int,
    phase: Phase,
    engine_id: EngineId | None,
    job_id: UUID | None,
    correlation_id: UUID,
    causation_id: UUID | None = None,
    provenance: Provenance = Provenance.AGENT,
) -> LedgerEventDraft | None:
    """Translate an EngineEvent to a LedgerEventDraft, or None if the event
    kind is unrecognized.

    Returns None (rather than raising) for unrecognized event types so a new
    loop version emitting a new event type does not crash vibey. The caller
    should log the skip and continue.
    """
    try:
        kind = EventKind(event.kind)
    except ValueError:
        # Unrecognized event kind - skip it gracefully.
        # The adapter should have already translated event_type -> kind using
        # LOOP_EVENT_MAP; if we get here, either the adapter is using a stale
        # map or the loop emitted something genuinely new.
        return None

    payload = dict(event.payload)
    return LedgerEventDraft(
        project_id=project_id,
        cycle=cycle,
        phase=phase,
        kind=kind,
        engine_id=engine_id,
        job_id=job_id,
        causation_id=causation_id,
        correlation_id=correlation_id,
        provenance=provenance,
        produced_at=event.at,
        payload=payload,
        digest=digest_event(payload),
    )


async def translate_run_iter(
    events: AsyncIterator[EngineEvent],
    *,
    project_id: UUID,
    cycle: int,
    phase: Phase,
    engine_id: EngineId | None,
    job_id: UUID | None,
    correlation_id: UUID,
) -> AsyncIterator[LedgerEventDraft]:
    """Translate a stream of EngineEvents to LedgerEventDrafts, skipping
    unrecognized event kinds gracefully."""
    causation_id: UUID | None = None
    async for event in events:
        draft = translate_event(
            event,
            project_id=project_id,
            cycle=cycle,
            phase=phase,
            engine_id=engine_id,
            job_id=job_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )
        if draft is not None:
            yield draft
        # else: unrecognized event kind, logged by caller if needed


__all__ = [
    "LedgerEventDraft",
    "UnknownEventKind",
    "canonical_bytes",
    "translate_event",
    "translate_run_iter",
]
