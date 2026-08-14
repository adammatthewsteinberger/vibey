import json
from collections.abc import Mapping
from uuid import UUID

import asyncpg

from vibey.application.dto import HumanGateRecord, HumanGateRequest


def _require(row: asyncpg.Record | None, *, context: str) -> asyncpg.Record:
    if row is None:
        raise LookupError(f"{context}: expected a row but got none")
    return row


def _row_to_record(row: asyncpg.Record) -> HumanGateRecord:
    return HumanGateRecord(
        gate_id=row["gate_id"],
        project_id=row["project_id"],
        job_id=row["job_id"],
        kind=row["kind"],
        prompt=row["prompt"],
        options=tuple(json.loads(row["options"])),
        default_answer=row["default_answer"],
        answer=json.loads(row["answer"]) if row["answer"] is not None else None,
        raised_at=row["raised_at"],
        timeout_at=row["timeout_at"],
        answered_at=row["answered_at"],
        answered_by=row["answered_by"],
    )


class PostgresHumanGateRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def raise_gate(
        self, project_id: UUID, job_id: UUID | None, request: HumanGateRequest
    ) -> HumanGateRecord:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO human_gate (
                    project_id, job_id, kind, prompt, options, default_answer, timeout_at
                ) VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7)
                RETURNING *
                """,
                project_id,
                job_id,
                request.kind,
                request.prompt,
                json.dumps(list(request.options)),
                request.default_answer,
                request.timeout_at,
            )
            row = _require(row, context="raise_gate insert")
            await conn.execute(f"NOTIFY vibey_gate_raised, '{row['gate_id']}'")
            return _row_to_record(row)

    async def answer(
        self, gate_id: UUID, *, answer: Mapping[str, object], answered_by: str
    ) -> HumanGateRecord:
        async with self._pool.acquire() as conn, conn.transaction():
            row = await conn.fetchrow(
                """
                UPDATE human_gate SET
                    answer = $2::jsonb, answered_at = now(), answered_by = $3
                WHERE gate_id = $1
                RETURNING *
                """,
                gate_id,
                json.dumps(dict(answer)),
                answered_by,
            )
            row = _require(row, context=f"answer: no gate {gate_id}")
            if row["job_id"] is not None:
                await conn.execute(
                    """
                    UPDATE job SET state = 'ready', updated_at = now()
                    WHERE id = $1 AND state = 'awaiting_human'
                    """,
                    row["job_id"],
                )
                await conn.execute(f"NOTIFY vibey_job_ready, '{row['project_id']}'")
            return _row_to_record(row)

    async def get(self, gate_id: UUID) -> HumanGateRecord | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM human_gate WHERE gate_id = $1", gate_id)
            return _row_to_record(row) if row is not None else None

    async def latest_for_job(self, job_id: UUID) -> HumanGateRecord | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM human_gate
                WHERE job_id = $1
                ORDER BY raised_at DESC, gate_id DESC
                LIMIT 1
                """,
                job_id,
            )
            return _row_to_record(row) if row is not None else None
