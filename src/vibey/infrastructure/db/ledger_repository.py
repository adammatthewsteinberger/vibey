"""The append-only event ledger, backed by the append_event() Postgres
function (migrations/0002_event.sql) which claims a gapless per-project seq
inside the same transaction as the insert -- the property rule R6 of the
no-loss gate depends on."""

import json
from collections.abc import Sequence
from uuid import UUID

import asyncpg

from vibey.domain.engine import EngineId
from vibey.domain.ledger import EventKind, LedgerEvent, Provenance, digest_event
from vibey.domain.phase import Phase
from vibey.infrastructure.engines.tailer import LedgerEventDraft
from vibey.infrastructure.ledger.redact import redact_payload


def _row_to_event(row: asyncpg.Record) -> LedgerEvent:
    return LedgerEvent(
        event_id=row["event_id"],
        project_id=row["project_id"],
        cycle=row["cycle"],
        phase=Phase(row["phase"]),
        seq=row["seq"],
        kind=EventKind(row["kind"]),
        engine_id=EngineId(row["engine_id"]) if row["engine_id"] is not None else None,
        job_id=row["job_id"],
        causation_id=row["causation_id"],
        correlation_id=row["correlation_id"],
        provenance=Provenance(row["provenance"]),
        produced_at=row["produced_at"],
        payload=json.loads(row["payload"]),
        digest=row["digest"],
    )


class PostgresLedgerRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def append(self, draft: LedgerEventDraft) -> LedgerEvent:
        # Redaction happens here, immediately before the payload is
        # persisted, and the digest is recomputed over what actually lands
        # in the column -- never over the pre-redaction payload the caller
        # built the draft from. A digest over unredacted content would be
        # useless for R6 range integrity once the stored payload differs.
        redacted_payload = redact_payload(draft.payload)
        digest = digest_event(redacted_payload)

        async with self._pool.acquire() as conn, conn.transaction():
            seq = await conn.fetchval(
                """
                SELECT append_event(
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::jsonb, $12
                )
                """,
                draft.project_id,
                draft.cycle,
                draft.phase.value,
                draft.kind.value,
                draft.engine_id.value if draft.engine_id is not None else None,
                draft.job_id,
                draft.causation_id,
                draft.correlation_id,
                draft.provenance.value,
                draft.produced_at,
                json.dumps(redacted_payload),
                digest,
            )
            row = await conn.fetchrow(
                "SELECT * FROM event WHERE project_id = $1 AND seq = $2",
                draft.project_id,
                seq,
            )
            if row is None:
                raise LookupError(f"append_event returned seq {seq} but no row exists")
            return _row_to_event(row)

    async def range(
        self, project_id: UUID, *, from_seq: int, to_seq: int
    ) -> tuple[LedgerEvent, ...]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM event
                WHERE project_id = $1 AND seq BETWEEN $2 AND $3
                ORDER BY seq
                """,
                project_id,
                from_seq,
                to_seq,
            )
            return tuple(_row_to_event(r) for r in rows)

    async def all_for_project(self, project_id: UUID) -> tuple[LedgerEvent, ...]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM event WHERE project_id = $1 ORDER BY seq", project_id
            )
            return tuple(_row_to_event(r) for r in rows)

    async def latest_seq(self, project_id: UUID) -> int:
        async with self._pool.acquire() as conn:
            value = await conn.fetchval(
                "SELECT max(seq) FROM event WHERE project_id = $1", project_id
            )
            return int(value) if value is not None else 0


def to_drafts(events: Sequence[LedgerEvent]) -> tuple[LedgerEventDraft, ...]:
    """Round-trips persisted events back into drafts, for tests that need
    to re-append a fixture range."""
    return tuple(
        LedgerEventDraft(
            project_id=e.project_id,
            cycle=e.cycle,
            phase=e.phase,
            kind=e.kind,
            engine_id=e.engine_id,
            job_id=e.job_id,
            causation_id=e.causation_id,
            correlation_id=e.correlation_id,
            provenance=e.provenance,
            produced_at=e.produced_at,
            payload=dict(e.payload),
            digest=e.digest,
        )
        for e in events
    )
