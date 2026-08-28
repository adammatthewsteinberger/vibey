# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Forward-only SQL migrations, applied in lexical order and tracked in
schema_migration(version, applied_at, checksum). An edited, already-applied
migration is a bug, not a convenience -- vibey migrate --check fails it."""

import hashlib
from dataclasses import dataclass
from pathlib import Path

import asyncpg

from vibey.domain.errors import VibeyError


class MigrationChecksumError(VibeyError):
    def __init__(self, version: str) -> None:
        self.version = version
        super().__init__(
            f"migration {version!r} has changed since it was applied "
            "-- edited migrations are not allowed"
        )


@dataclass(frozen=True, slots=True)
class Migration:
    version: str
    path: Path
    sql: str
    checksum: str


def _checksum(sql: str) -> str:
    return hashlib.sha256(sql.encode()).hexdigest()


def discover_migrations(directory: Path) -> tuple[Migration, ...]:
    migrations = []
    for path in sorted(directory.glob("*.sql")):
        sql = path.read_text()
        migrations.append(Migration(version=path.stem, path=path, sql=sql, checksum=_checksum(sql)))
    return tuple(migrations)


_ENSURE_SCHEMA_MIGRATION_TABLE = """
CREATE TABLE IF NOT EXISTS schema_migration (
    version     text PRIMARY KEY,
    applied_at  timestamptz NOT NULL DEFAULT now(),
    checksum    text NOT NULL
);
"""


async def apply_migrations(
    conn: asyncpg.pool.PoolConnectionProxy | asyncpg.Connection,
    migrations: tuple[Migration, ...],
    *,
    check_only: bool = False,
) -> tuple[str, ...]:
    """Applies pending migrations in order. Raises MigrationChecksumError if
    an already-applied migration's file has changed. Returns the versions
    applied this call (empty in check_only mode)."""
    await conn.execute(_ENSURE_SCHEMA_MIGRATION_TABLE)

    applied_rows = await conn.fetch("SELECT version, checksum FROM schema_migration")
    applied = {row["version"]: row["checksum"] for row in applied_rows}

    newly_applied = []
    for migration in migrations:
        if migration.version in applied:
            if applied[migration.version] != migration.checksum:
                raise MigrationChecksumError(migration.version)
            continue

        if check_only:
            continue

        async with conn.transaction():
            await conn.execute(migration.sql)
            await conn.execute(
                "INSERT INTO schema_migration (version, checksum) VALUES ($1, $2)",
                migration.version,
                migration.checksum,
            )
        newly_applied.append(migration.version)

    return tuple(newly_applied)
