# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Persists every handoff attempt, including its violations, so gate
quality is queryable (data-model.md §3.7): "how often does claudeloop ->
codexloop need two attempts?" is a query, not a guess."""

import json
from collections.abc import Mapping
from dataclasses import asdict
from uuid import UUID

import asyncpg

from vibey.domain.handoff import GateResult, HandoffEnvelope


def _json_default(value: object) -> object:
    if isinstance(value, UUID):
        return str(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "value"):  # StrEnum / IntEnum members
        return value.value
    raise TypeError(f"not JSON serializable: {type(value).__name__}")


def envelope_to_json(envelope: HandoffEnvelope) -> str:
    return json.dumps(asdict(envelope), default=_json_default, sort_keys=True)


def violations_to_json(result: GateResult) -> str:
    return json.dumps([asdict(v) for v in result.violations], default=_json_default, sort_keys=True)


class PostgresHandoffRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def record(self, envelope: HandoffEnvelope) -> UUID:
        async with self._pool.acquire() as conn:
            handoff_id = await conn.fetchval(
                """
                INSERT INTO handoff (
                    handoff_id, project_id, cycle, phase, job_id, from_engine,
                    to_engine, reason, from_seq, to_seq, range_digest, envelope,
                    gate_mode, gate_attempts, gate_violations, accepted
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12::jsonb,
                    $13, $14, $15::jsonb, $16
                )
                RETURNING handoff_id
                """,
                envelope.handoff_id,
                envelope.project_id,
                envelope.cycle,
                envelope.phase.value,
                None,  # job_id: linked separately by the caller if applicable
                envelope.from_engine.value if envelope.from_engine is not None else None,
                envelope.to_engine.value,
                envelope.reason.value,
                envelope.ledger_ref.from_seq,
                envelope.ledger_ref.to_seq,
                envelope.ledger_ref.digest,
                envelope_to_json(envelope),
                envelope.gate.mode.value,
                envelope.gate.attempts,
                violations_to_json(envelope.gate),
                envelope.gate.ok,
            )
            return UUID(str(handoff_id))

    async def get(self, handoff_id: UUID) -> Mapping[str, object] | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM handoff WHERE handoff_id = $1", handoff_id)
            if row is None:
                return None
            return _row_to_dict(row)

    async def list_for_pair(
        self, project_id: UUID, *, from_engine: str | None, to_engine: str
    ) -> tuple[Mapping[str, object], ...]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM handoff
                WHERE project_id = $1 AND to_engine = $2
                  AND from_engine IS NOT DISTINCT FROM $3
                ORDER BY created_at
                """,
                project_id,
                to_engine,
                from_engine,
            )
            return tuple(_row_to_dict(r) for r in rows)


def _row_to_dict(row: asyncpg.Record) -> dict[str, object]:
    return {
        "handoff_id": row["handoff_id"],
        "project_id": row["project_id"],
        "cycle": row["cycle"],
        "phase": row["phase"],
        "from_engine": row["from_engine"],
        "to_engine": row["to_engine"],
        "reason": row["reason"],
        "from_seq": row["from_seq"],
        "to_seq": row["to_seq"],
        "range_digest": row["range_digest"],
        "envelope": json.loads(row["envelope"]),
        "gate_mode": row["gate_mode"],
        "gate_attempts": row["gate_attempts"],
        "gate_violations": json.loads(row["gate_violations"]),
        "accepted": row["accepted"],
    }
