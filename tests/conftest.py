# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Root test configuration — per-worker database via PostgreSQL template pattern.

Session startup creates ``vibey_test_template`` (migrated once, reused across
sessions) and clones it into ``vibey_test_<worker_id>`` for this process.
``VIBEY_TEST_DATABASE_URL`` is repointed so every downstream fixture and test
helper picks up the isolated per-worker database transparently.
"""

import asyncio
import contextlib
import getpass
import os
from pathlib import Path

import asyncpg
import pytest

from vibey.infrastructure.db.migrator import apply_migrations, discover_migrations

_MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"
_TEMPLATE_DB = "vibey_test_template"
_BASE_DSN: str | None = None


def _resolve_base_dsn() -> str:
    return os.environ.get(
        "_VIBEY_TEST_BASE_DSN",
        os.environ.get(
            "VIBEY_TEST_DATABASE_URL",
            f"postgresql://{getpass.getuser()}@localhost:5432/vibey_test",
        ),
    )


def _replace_dbname(dsn: str, dbname: str) -> str:
    base, _ = dsn.rsplit("/", 1)
    return f"{base}/{dbname}"


def _worker_id() -> str:
    return os.environ.get("PYTEST_XDIST_WORKER", "main")


def _worker_db_name() -> str:
    run_id = os.environ.get("PYTEST_XDIST_TESTRUNUID", "main")
    return f"vibey_test_{_worker_id()}_{run_id}"


async def _setup(base_dsn: str) -> str:
    """Create template (if needed) and per-worker clone; return worker DSN."""
    admin_dsn = _replace_dbname(base_dsn, "postgres")
    wdb = _worker_db_name()

    conn = await asyncpg.connect(admin_dsn)
    try:
        # Serialise template creation + clone so no process connects to the
        # template while another clones from it.
        await conn.execute("SELECT pg_advisory_lock(hashtext($1))", _TEMPLATE_DB)
        try:
            exists = await conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1",
                _TEMPLATE_DB,
            )
            if not exists:
                await conn.execute(f'CREATE DATABASE "{_TEMPLATE_DB}"')

            tmpl_conn = await asyncpg.connect(
                _replace_dbname(base_dsn, _TEMPLATE_DB),
            )
            try:
                migrations = discover_migrations(_MIGRATIONS_DIR)
                await apply_migrations(tmpl_conn, migrations)
            finally:
                await tmpl_conn.close()

            # Drop-if-exists handles crashed prior runs (AC-14).
            await conn.execute(
                "SELECT pg_terminate_backend(pid) "
                "FROM pg_stat_activity "
                "WHERE datname = $1 AND pid <> pg_backend_pid()",
                wdb,
            )
            await conn.execute(f'DROP DATABASE IF EXISTS "{wdb}"')
            await conn.execute(
                f'CREATE DATABASE "{wdb}" TEMPLATE "{_TEMPLATE_DB}"',
            )
        finally:
            await conn.execute(
                "SELECT pg_advisory_unlock(hashtext($1))",
                _TEMPLATE_DB,
            )
    finally:
        await conn.close()

    return _replace_dbname(base_dsn, wdb)


async def _teardown(base_dsn: str) -> None:
    wdb = _worker_db_name()
    admin_dsn = _replace_dbname(base_dsn, "postgres")
    conn = await asyncpg.connect(admin_dsn)
    try:
        await conn.execute(
            "SELECT pg_terminate_backend(pid) "
            "FROM pg_stat_activity "
            "WHERE datname = $1 AND pid <> pg_backend_pid()",
            wdb,
        )
        await conn.execute(f'DROP DATABASE IF EXISTS "{wdb}"')
    finally:
        await conn.close()


def pytest_configure(config: pytest.Config) -> None:
    global _BASE_DSN
    _BASE_DSN = _resolve_base_dsn()
    os.environ["_VIBEY_TEST_BASE_DSN"] = _BASE_DSN
    worker_dsn = asyncio.run(_setup(_BASE_DSN))
    os.environ["VIBEY_TEST_DATABASE_URL"] = worker_dsn


def pytest_unconfigure(config: pytest.Config) -> None:
    if _BASE_DSN is not None:
        with contextlib.suppress(Exception):
            asyncio.run(_teardown(_BASE_DSN))
