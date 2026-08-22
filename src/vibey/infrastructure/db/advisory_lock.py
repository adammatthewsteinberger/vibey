# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Postgres advisory lock scoped to (project_id, cycle) -- the
IntegrationLock implementation that lets multiple workers safely share one
integration branch.

Session-level advisory locks live on the connection that took them, so a
held lock pins its pooled connection out of the pool until release. That
is deliberate: releasing the connection back would silently drop the lock
the moment another query reused the session. try_acquire never blocks
(``pg_try_advisory_lock``) -- contention is the caller's cue to defer the
job, not to wait.
"""

import hashlib
from typing import Any
from uuid import UUID

import asyncpg


def lock_key(project_id: UUID, cycle: int) -> int:
    """A stable signed-64-bit key for pg advisory locks, namespaced so it
    can never collide with any other advisory-lock use in the database."""
    digest = hashlib.sha256(f"vibey.integrate:{project_id}:{cycle}".encode()).digest()
    return int.from_bytes(digest[:8], "big", signed=True)


class PostgresAdvisoryLock:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool
        self._held: dict[tuple[UUID, int], Any] = {}

    async def try_acquire(self, project_id: UUID, cycle: int) -> bool:
        key = (project_id, cycle)
        if key in self._held:
            # Another loop sharing this instance holds the branch; treat
            # it as contention rather than silently re-entering.
            return False
        conn = await self._pool.acquire()
        acquired = await conn.fetchval(
            "SELECT pg_try_advisory_lock($1)", lock_key(project_id, cycle)
        )
        if not acquired:
            await self._pool.release(conn)
            return False
        self._held[key] = conn
        return True

    async def release(self, project_id: UUID, cycle: int) -> None:
        conn = self._held.pop((project_id, cycle), None)
        if conn is None:
            return
        await conn.fetchval("SELECT pg_advisory_unlock($1)", lock_key(project_id, cycle))
        await self._pool.release(conn)
