# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
from pathlib import Path

import asyncpg
import pytest

from vibey.infrastructure.db.migrator import (
    MigrationChecksumError,
    apply_migrations,
    discover_migrations,
)

MIGRATIONS_DIR = Path(__file__).resolve().parents[3] / "migrations"


def _write_migration(tmp_path: Path, name: str, sql: str) -> Path:
    path = tmp_path / name
    path.write_text(sql)
    return path


async def test_discover_migrations_returns_real_migrations_in_lexical_order() -> None:
    migrations = discover_migrations(MIGRATIONS_DIR)

    versions = [m.version for m in migrations]
    assert versions == sorted(versions)
    assert versions[0] == "0001_project"
    assert "0008_human_gate_artifact_budget" in versions


async def test_apply_all_real_migrations_to_a_fresh_database(pg_conn: asyncpg.Connection) -> None:
    migrations = discover_migrations(MIGRATIONS_DIR)

    applied = await apply_migrations(pg_conn, migrations)

    assert applied == tuple(m.version for m in migrations)

    tables = await pg_conn.fetch(
        "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
    )
    table_names = {row["tablename"] for row in tables}
    for expected in (
        "project",
        "event",
        "job",
        "job_dependency",
        "work_item",
        "open_item",
        "handoff",
        "engine_health",
        "rotation_cursor",
        "human_gate",
        "artifact",
        "budget_ledger",
        "schema_migration",
    ):
        assert expected in table_names


async def test_applying_migrations_twice_is_a_no_op(pg_conn: asyncpg.Connection) -> None:
    migrations = discover_migrations(MIGRATIONS_DIR)

    first = await apply_migrations(pg_conn, migrations)
    second = await apply_migrations(pg_conn, migrations)

    assert first == tuple(m.version for m in migrations)
    assert second == ()


async def test_applying_migrations_over_seeded_fixture_data(pg_conn: asyncpg.Connection) -> None:
    migrations = discover_migrations(MIGRATIONS_DIR)
    await apply_migrations(pg_conn, migrations)

    project_id = await pg_conn.fetchval(
        "INSERT INTO project (name, repo_path, config) VALUES ($1, $2, $3::jsonb) RETURNING id",
        "demo",
        "/tmp/demo",
        "{}",
    )
    assert project_id is not None

    # Re-applying over a database with real rows must still be a no-op, not
    # a destructive re-run.
    applied_again = await apply_migrations(pg_conn, migrations)
    assert applied_again == ()

    name = await pg_conn.fetchval("SELECT name FROM project WHERE id = $1", project_id)
    assert name == "demo"


async def test_edited_migration_fails_the_checksum_guard(
    pg_conn: asyncpg.Connection, tmp_path: Path
) -> None:
    original_sql = "CREATE TABLE t (id serial PRIMARY KEY);"
    path = _write_migration(tmp_path, "0001_t.sql", original_sql)
    migrations = discover_migrations(tmp_path)
    await apply_migrations(pg_conn, migrations)

    # Edit the already-applied migration on disk.
    path.write_text("CREATE TABLE t (id serial PRIMARY KEY, extra text);")
    edited_migrations = discover_migrations(tmp_path)

    with pytest.raises(MigrationChecksumError) as exc_info:
        await apply_migrations(pg_conn, edited_migrations)

    assert exc_info.value.version == "0001_t"


async def test_check_only_mode_does_not_apply_pending_migrations(
    pg_conn: asyncpg.Connection, tmp_path: Path
) -> None:
    _write_migration(tmp_path, "0001_t.sql", "CREATE TABLE t (id serial PRIMARY KEY);")
    migrations = discover_migrations(tmp_path)

    applied = await apply_migrations(pg_conn, migrations, check_only=True)

    assert applied == ()
    exists = await pg_conn.fetchval("SELECT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 't')")
    assert exists is False


async def test_check_only_mode_still_catches_a_checksum_mismatch(
    pg_conn: asyncpg.Connection, tmp_path: Path
) -> None:
    path = _write_migration(tmp_path, "0001_t.sql", "CREATE TABLE t (id serial PRIMARY KEY);")
    migrations = discover_migrations(tmp_path)
    await apply_migrations(pg_conn, migrations)

    path.write_text("CREATE TABLE t (id serial PRIMARY KEY, extra text);")
    edited_migrations = discover_migrations(tmp_path)

    with pytest.raises(MigrationChecksumError):
        await apply_migrations(pg_conn, edited_migrations, check_only=True)
