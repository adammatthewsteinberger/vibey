# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""FullLedger writer: <worktree>/.vibey/handoff/ledger.jsonl, one JSON
object per line ordered by seq -- the complete, unabridged history handed
to every receiving engine (handoff-protocol.md §4.1). The digest in the
returned LedgerRef is exactly domain.ledger.digest_range(events), so R6 of
the no-loss gate can verify the file on disk against the ref without
re-reading the database."""

import json
from collections.abc import Sequence
from pathlib import Path

from vibey.domain.handoff import LedgerRef
from vibey.domain.ledger import LedgerEvent, digest_range


def _event_to_json_line(event: LedgerEvent) -> str:
    return json.dumps(
        {
            "event_id": str(event.event_id),
            "project_id": str(event.project_id),
            "cycle": event.cycle,
            "phase": event.phase.value,
            "seq": event.seq,
            "kind": event.kind.value,
            "engine_id": event.engine_id.value if event.engine_id is not None else None,
            "job_id": str(event.job_id) if event.job_id is not None else None,
            "causation_id": str(event.causation_id) if event.causation_id is not None else None,
            "correlation_id": str(event.correlation_id),
            "provenance": event.provenance.value,
            "produced_at": event.produced_at.isoformat(),
            "payload": event.payload,
            "digest": event.digest,
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def write_full_ledger(
    events: Sequence[LedgerEvent], path: Path, *, uri: str = "handoff/ledger.jsonl"
) -> LedgerRef:
    ordered = sorted(events, key=lambda e: e.seq)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for event in ordered:
            f.write(_event_to_json_line(event) + "\n")

    if not ordered:
        return LedgerRef(uri=uri, from_seq=0, to_seq=0, event_count=0, digest=digest_range(()))

    return LedgerRef(
        uri=uri,
        from_seq=ordered[0].seq,
        to_seq=ordered[-1].seq,
        event_count=len(ordered),
        digest=digest_range(ordered),
    )


def read_full_ledger_line_count(path: Path) -> int:
    """A cheap sanity check used by tests and `vibey doctor`: the file's
    line count should equal the ref's event_count."""
    with path.open() as f:
        return sum(1 for line in f if line.strip())
