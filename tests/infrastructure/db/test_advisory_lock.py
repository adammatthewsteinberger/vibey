# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""PostgresAdvisoryLock: real cross-connection mutual exclusion."""

from uuid import uuid4

import asyncpg

from vibey.infrastructure.db.advisory_lock import PostgresAdvisoryLock, lock_key


def test_lock_key_is_stable_and_scoped() -> None:
    project_id = uuid4()
    assert lock_key(project_id, 1) == lock_key(project_id, 1)
    assert lock_key(project_id, 1) != lock_key(project_id, 2)
    assert lock_key(project_id, 1) != lock_key(uuid4(), 1)
    # Fits pg's signed bigint.
    assert -(2**63) <= lock_key(project_id, 1) < 2**63


async def test_two_workers_contend_and_hand_over(migrated_pool: asyncpg.Pool) -> None:
    project_id = uuid4()
    worker_a = PostgresAdvisoryLock(migrated_pool)
    worker_b = PostgresAdvisoryLock(migrated_pool)

    assert await worker_a.try_acquire(project_id, 1) is True
    assert await worker_b.try_acquire(project_id, 1) is False

    # A different cycle is a different branch: no contention.
    assert await worker_b.try_acquire(project_id, 2) is True
    await worker_b.release(project_id, 2)

    await worker_a.release(project_id, 1)
    assert await worker_b.try_acquire(project_id, 1) is True
    await worker_b.release(project_id, 1)


async def test_same_instance_reports_contention_not_reentry(
    migrated_pool: asyncpg.Pool,
) -> None:
    project_id = uuid4()
    lock = PostgresAdvisoryLock(migrated_pool)

    assert await lock.try_acquire(project_id, 1) is True
    assert await lock.try_acquire(project_id, 1) is False
    await lock.release(project_id, 1)


async def test_release_without_a_held_lock_is_a_no_op(migrated_pool: asyncpg.Pool) -> None:
    lock = PostgresAdvisoryLock(migrated_pool)
    await lock.release(uuid4(), 1)
