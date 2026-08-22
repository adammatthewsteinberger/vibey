# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Postgres repository for rotation_cursor table.

The rotation_cursor table persists the SWRR (smooth weighted round robin) state
per project per engine. This state is updated transactionally with job leasing
to ensure crash-safety.
"""

from uuid import UUID

import asyncpg

from vibey.application.dto import RotationCursor
from vibey.domain.engine import EngineId


class PostgresRotationCursorRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def get(self, project_id: UUID, engine_id: EngineId) -> RotationCursor | None:
        """Get cursor for one engine, or None if not initialized."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM rotation_cursor WHERE project_id = $1 AND engine_id = $2",
                project_id,
                engine_id.value,
            )
            if row is None:
                return None
            return RotationCursor(
                project_id=row["project_id"],
                engine_id=EngineId(row["engine_id"]),
                current=row["current"],
                order=row["order"],
            )

    async def list_for_project(self, project_id: UUID) -> tuple[RotationCursor, ...]:
        """Get all cursors for a project."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                'SELECT * FROM rotation_cursor WHERE project_id = $1 ORDER BY "order"',
                project_id,
            )
            return tuple(
                RotationCursor(
                    project_id=row["project_id"],
                    engine_id=EngineId(row["engine_id"]),
                    current=row["current"],
                    order=row["order"],
                )
                for row in rows
            )

    async def upsert(self, cursor: RotationCursor) -> RotationCursor:
        """Insert or update a cursor."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO rotation_cursor (project_id, engine_id, current, "order")
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (project_id, engine_id) DO UPDATE SET
                    current = EXCLUDED.current,
                    "order" = EXCLUDED."order"
                RETURNING *
                """,
                cursor.project_id,
                cursor.engine_id.value,
                cursor.current,
                cursor.order,
            )
            return RotationCursor(
                project_id=row["project_id"],
                engine_id=EngineId(row["engine_id"]),
                current=row["current"],
                order=row["order"],
            )

    async def update_many(
        self, project_id: UUID, cursors: tuple[RotationCursor, ...]
    ) -> tuple[RotationCursor, ...]:
        """Update multiple cursors atomically (used after SWRR selection).

        This is the critical operation that must happen transactionally with
        job leasing so a crash cannot double-advance the cursor.
        """
        async with self._pool.acquire() as conn, conn.transaction():
            results = []
            for cursor in cursors:
                row = await conn.fetchrow(
                    """
                        INSERT INTO rotation_cursor (project_id, engine_id, current, "order")
                        VALUES ($1, $2, $3, $4)
                        ON CONFLICT (project_id, engine_id) DO UPDATE SET
                            current = EXCLUDED.current,
                            "order" = EXCLUDED."order"
                        RETURNING *
                        """,
                    cursor.project_id,
                    cursor.engine_id.value,
                    cursor.current,
                    cursor.order,
                )
                results.append(
                    RotationCursor(
                        project_id=row["project_id"],
                        engine_id=EngineId(row["engine_id"]),
                        current=row["current"],
                        order=row["order"],
                    )
                )
            return tuple(results)

    async def initialize_for_project(
        self, project_id: UUID, engines: tuple[EngineId, ...]
    ) -> tuple[RotationCursor, ...]:
        """Initialize cursors for all engines in a project.

        Sets current=0 and order based on engine position in the tuple.
        Idempotent - only inserts if not present.
        """
        async with self._pool.acquire() as conn, conn.transaction():
            results = []
            for idx, engine_id in enumerate(engines):
                row = await conn.fetchrow(
                    """
                        INSERT INTO rotation_cursor (project_id, engine_id, current, "order")
                        VALUES ($1, $2, 0, $3)
                        ON CONFLICT (project_id, engine_id) DO NOTHING
                        RETURNING *
                        """,
                    project_id,
                    engine_id.value,
                    idx,
                )
                if row:
                    results.append(
                        RotationCursor(
                            project_id=row["project_id"],
                            engine_id=EngineId(row["engine_id"]),
                            current=row["current"],
                            order=row["order"],
                        )
                    )

            # Return all cursors for the project
            rows = await conn.fetch(
                'SELECT * FROM rotation_cursor WHERE project_id = $1 ORDER BY "order"',
                project_id,
            )
            return tuple(
                RotationCursor(
                    project_id=row["project_id"],
                    engine_id=EngineId(row["engine_id"]),
                    current=row["current"],
                    order=row["order"],
                )
                for row in rows
            )


__all__ = ["PostgresRotationCursorRepository"]
