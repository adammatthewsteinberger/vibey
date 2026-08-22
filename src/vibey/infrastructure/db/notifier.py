# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""LISTEN/NOTIFY wakeup for job-ready events, with a timeout that doubles as
the 5-second poll fallback: a missed or coalesced notification costs
latency, never correctness, because the worker loop re-polls the queue on
every wakeup regardless of why it woke."""

import asyncio
from datetime import timedelta
from uuid import UUID

import asyncpg

_CHANNEL = "vibey_job_ready"


class PostgresJobReadyNotifier:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._conn: asyncpg.Connection | None = None
        self._waiters: dict[str, list[asyncio.Future[bool]]] = {}

    async def connect(self) -> None:
        self._conn = await asyncpg.connect(self._dsn)
        await self._conn.add_listener(_CHANNEL, self._on_notify)

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.remove_listener(_CHANNEL, self._on_notify)
            await self._conn.close()
            self._conn = None

    def _on_notify(self, connection: object, pid: int, channel: str, payload: str) -> None:
        for fut in self._waiters.pop(payload, []):
            if not fut.done():
                fut.set_result(True)

    async def wait_for_job_ready(self, project_id: UUID, *, timeout: timedelta) -> bool:
        loop = asyncio.get_running_loop()
        fut: asyncio.Future[bool] = loop.create_future()
        key = str(project_id)
        self._waiters.setdefault(key, []).append(fut)
        try:
            return await asyncio.wait_for(fut, timeout=timeout.total_seconds())
        except TimeoutError:
            return False
        finally:
            waiters = self._waiters.get(key)
            if waiters and fut in waiters:
                waiters.remove(fut)
                if not waiters:
                    del self._waiters[key]
