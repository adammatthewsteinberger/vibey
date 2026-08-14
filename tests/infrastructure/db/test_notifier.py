import asyncio
from datetime import timedelta
from uuid import UUID

import asyncpg
import pytest

from vibey.infrastructure.db.notifier import PostgresJobReadyNotifier

from .conftest import TEST_DATABASE_URL


@pytest.fixture
def notifier() -> PostgresJobReadyNotifier:
    return PostgresJobReadyNotifier(TEST_DATABASE_URL)


async def test_wait_for_job_ready_returns_true_when_notified(
    migrated_pool: asyncpg.Pool, project_id: UUID, notifier: PostgresJobReadyNotifier
) -> None:
    await notifier.connect()
    try:
        wait_task = asyncio.ensure_future(
            notifier.wait_for_job_ready(project_id, timeout=timedelta(seconds=5))
        )
        await asyncio.sleep(0.05)  # let the LISTEN register before we NOTIFY

        async with migrated_pool.acquire() as conn:
            await conn.execute(f"NOTIFY vibey_job_ready, '{project_id}'")

        result = await asyncio.wait_for(wait_task, timeout=2.0)
        assert result is True
    finally:
        await notifier.close()


async def test_wait_for_job_ready_falls_back_to_timeout_when_not_notified(
    migrated_pool: asyncpg.Pool, project_id: UUID, notifier: PostgresJobReadyNotifier
) -> None:
    await notifier.connect()
    try:
        result = await notifier.wait_for_job_ready(project_id, timeout=timedelta(milliseconds=50))
        assert result is False
    finally:
        await notifier.close()


async def test_notify_for_a_different_project_does_not_wake_this_waiter(
    migrated_pool: asyncpg.Pool, project_id: UUID, notifier: PostgresJobReadyNotifier
) -> None:
    other_project_id = UUID(int=project_id.int ^ 1)
    await notifier.connect()
    try:
        wait_task = asyncio.ensure_future(
            notifier.wait_for_job_ready(project_id, timeout=timedelta(milliseconds=200))
        )
        await asyncio.sleep(0.05)

        async with migrated_pool.acquire() as conn:
            await conn.execute(f"NOTIFY vibey_job_ready, '{other_project_id}'")

        result = await wait_task
        assert result is False
    finally:
        await notifier.close()
