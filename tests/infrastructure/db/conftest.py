# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
import getpass
import os
from collections.abc import AsyncIterator
from pathlib import Path
from uuid import UUID

import asyncpg
import pytest
import pytest_asyncio

from vibey.infrastructure.db.migrator import apply_migrations, discover_migrations

TEST_DATABASE_URL = os.environ.get(
    "VIBEY_TEST_DATABASE_URL",
    f"postgresql://{getpass.getuser()}@localhost:5432/vibey_test",
)

MIGRATIONS_DIR = Path(__file__).resolve().parents[3] / "migrations"


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    for item in items:
        item.add_marker(pytest.mark.integration)


@pytest_asyncio.fixture
async def pg_conn() -> AsyncIterator[asyncpg.Connection]:
    conn = await asyncpg.connect(TEST_DATABASE_URL)
    await conn.execute("DROP SCHEMA public CASCADE")
    await conn.execute("CREATE SCHEMA public")
    try:
        yield conn
    finally:
        await conn.close()


@pytest_asyncio.fixture
async def pg_pool() -> AsyncIterator[asyncpg.Pool]:
    pool = await asyncpg.create_pool(TEST_DATABASE_URL, min_size=1, max_size=10)
    assert pool is not None
    async with pool.acquire() as conn:
        await conn.execute("DROP SCHEMA public CASCADE")
        await conn.execute("CREATE SCHEMA public")
    try:
        yield pool
    finally:
        await pool.close()


@pytest_asyncio.fixture
async def migrated_pool(pg_pool: asyncpg.Pool) -> asyncpg.Pool:
    async with pg_pool.acquire() as conn:
        migrations = discover_migrations(MIGRATIONS_DIR)
        await apply_migrations(conn, migrations)
    return pg_pool


@pytest_asyncio.fixture
async def project_id(migrated_pool: asyncpg.Pool) -> UUID:
    async with migrated_pool.acquire() as conn:
        pid = await conn.fetchval(
            "INSERT INTO project (name, repo_path, config) VALUES ($1, $2, $3::jsonb) RETURNING id",
            "demo",
            "/tmp/demo",
            "{}",
        )
        assert pid is not None
        return UUID(str(pid))
