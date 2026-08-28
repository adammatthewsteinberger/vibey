# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from uuid import UUID

import asyncpg

from vibey.application.dto import EngineHealthRecord
from vibey.domain.engine import EngineId


def _row_to_record(row: asyncpg.Record) -> EngineHealthRecord:
    return EngineHealthRecord(
        project_id=row["project_id"],
        # The column is text; EngineHealthRecord declares EngineId. Leaving
        # the raw str here propagated all the way into RotationCursor and
        # crashed PostgresRotationCursorRepository.update_many's
        # `.value` access the first time EngineSelector ran against real
        # Postgres -- every fake-backed test stored real EngineId values, so
        # only a Postgres round-trip regression test catches this.
        engine_id=EngineId(row["engine_id"]),
        installed=row["installed"],
        version=row["version"],
        conformance_ok=row["conformance_ok"],
        conformance_at=row["conformance_at"],
        auth_ok_at=row["auth_ok_at"],
        circuit=row["circuit"],
        capacity_state=row["capacity_state"],
        resets_at=row["resets_at"],
        probe_next_at=row["probe_next_at"],
        probe_attempt=row["probe_attempt"],
        consecutive_fail=row["consecutive_fail"],
        ewma_failure=row["ewma_failure"],
        cost_usd_cycle=float(row["cost_usd_cycle"]),
        selected_count=row["selected_count"],
    )


class PostgresEngineHealthRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def get(self, project_id: UUID, engine_id: str) -> EngineHealthRecord | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM engine_health WHERE project_id = $1 AND engine_id = $2",
                project_id,
                engine_id,
            )
            return _row_to_record(row) if row is not None else None

    async def upsert(self, record: EngineHealthRecord) -> EngineHealthRecord:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO engine_health (
                    project_id, engine_id, installed, version, conformance_ok,
                    conformance_at, auth_ok_at, circuit, capacity_state, resets_at,
                    probe_next_at, probe_attempt, consecutive_fail, ewma_failure,
                    cost_usd_cycle, selected_count
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8::circuit_state, $9, $10,
                    $11, $12, $13, $14, $15, $16
                )
                ON CONFLICT (project_id, engine_id) DO UPDATE SET
                    installed        = EXCLUDED.installed,
                    version          = EXCLUDED.version,
                    conformance_ok   = EXCLUDED.conformance_ok,
                    conformance_at   = EXCLUDED.conformance_at,
                    auth_ok_at       = EXCLUDED.auth_ok_at,
                    circuit          = EXCLUDED.circuit,
                    capacity_state   = EXCLUDED.capacity_state,
                    resets_at        = EXCLUDED.resets_at,
                    probe_next_at    = EXCLUDED.probe_next_at,
                    probe_attempt    = EXCLUDED.probe_attempt,
                    consecutive_fail = EXCLUDED.consecutive_fail,
                    ewma_failure     = EXCLUDED.ewma_failure,
                    cost_usd_cycle   = EXCLUDED.cost_usd_cycle,
                    selected_count   = EXCLUDED.selected_count
                RETURNING *
                """,
                record.project_id,
                record.engine_id,
                record.installed,
                record.version,
                record.conformance_ok,
                record.conformance_at,
                record.auth_ok_at,
                record.circuit,
                record.capacity_state,
                record.resets_at,
                record.probe_next_at,
                record.probe_attempt,
                record.consecutive_fail,
                record.ewma_failure,
                record.cost_usd_cycle,
                record.selected_count,
            )
            if row is None:
                raise LookupError(f"upsert: no row returned for engine_health {record.engine_id}")
            return _row_to_record(row)

    async def list_for_project(self, project_id: UUID) -> tuple[EngineHealthRecord, ...]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM engine_health WHERE project_id = $1 ORDER BY engine_id",
                project_id,
            )
            return tuple(_row_to_record(r) for r in rows)
