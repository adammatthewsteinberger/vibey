"""Cluster preflight checks.

The database arms run against real Postgres, never a mock: a check whose
whole job is to notice a misconfigured connection is worthless if the
connection is faked.
"""

import os
from pathlib import Path

import asyncpg
import pytest

from vibey.bootstrap import build_app, migrations_dir
from vibey.infrastructure.cluster_preflight import (
    ClusterCheck,
    all_ok,
    check_database,
    check_dsn_resolves_cluster_wide,
    check_engine_auth,
    check_migrations,
    check_not_root,
    check_workspace_writable,
    run_cluster_preflight,
)

pytestmark = pytest.mark.integration


def _test_dsn() -> str:
    return os.environ.get(
        "VIBEY_TEST_DATABASE_URL",
        f"postgresql://{os.environ.get('USER', 'postgres')}@localhost:5432/vibey_test",
    )


# An unroutable port on loopback: refused immediately rather than hanging.
_DEAD_DSN = "postgresql://nobody@127.0.0.1:1/nothing"


@pytest.mark.parametrize(
    ("dsn", "expected_ok"),
    [
        ("postgresql://u:p@db.ns.svc.cluster.local:5432/vibey", True),
        ("postgresql://u:p@localhost:5432/vibey", True),
        ("postgresql://u:p@10.96.0.10:5432/vibey", True),
        ("postgresql://u:p@[::1]:5432/vibey", True),
        ("postgresql://u:p@vibey-postgres:5432/vibey", False),
    ],
)
def test_dsn_qualification_is_judged_by_cross_namespace_resolvability(
    dsn: str, expected_ok: bool
) -> None:
    """The bare-name case is the one that shipped: it works for the worker,
    which is in the namespace, and fails for KEDA's operator, which is not."""
    assert check_dsn_resolves_cluster_wide(dsn).ok is expected_ok


def test_dsn_without_a_host_is_a_failure_not_a_crash() -> None:
    check = check_dsn_resolves_cluster_wide("postgresql:///vibey")
    assert not check.ok
    assert "no host" in check.detail


def test_bare_host_failure_names_the_fix() -> None:
    check = check_dsn_resolves_cluster_wide("postgresql://u@vibey-postgres:5432/v")
    assert "svc" in check.detail


def test_root_fails_and_any_other_uid_passes() -> None:
    assert not check_not_root(0).ok
    assert check_not_root(10001).ok


def test_workspace_writable(tmp_path: Path) -> None:
    assert check_workspace_writable(tmp_path).ok


def test_workspace_unwritable_reports_the_reason(tmp_path: Path) -> None:
    """A read-only or wrongly-owned volume fails at the first worktree,
    long after the pod reports Ready."""
    check = check_workspace_writable(tmp_path / "does-not-exist")
    assert not check.ok
    assert "does-not-exist" in check.detail


def test_no_engine_binaries_is_the_scripted_image_not_a_fault() -> None:
    check = check_engine_auth({}, which=lambda _binary: None)
    assert check.ok
    assert "scripted" in check.detail


def test_installed_engine_without_credentials_fails() -> None:
    """Subscription login is a TTY flow; in a cluster an engine binary with
    no API key can never authenticate."""
    check = check_engine_auth({}, which=lambda binary: f"/usr/bin/{binary}")
    assert not check.ok
    assert "unauthenticated" in check.detail


def test_installed_engine_with_credentials_passes() -> None:
    environ = {
        "ANTHROPIC_API_KEY": "x",
        "OPENAI_API_KEY": "x",
        "CURSOR_API_KEY": "x",
        "GOOGLE_API_KEY": "x",
    }
    check = check_engine_auth(environ, which=lambda binary: f"/usr/bin/{binary}")
    assert check.ok


async def test_database_check_connects_and_hands_back_the_connection() -> None:
    check, conn = await check_database(_test_dsn())
    assert check.ok
    assert conn is not None
    await conn.close()


async def test_database_check_reports_an_unreachable_host() -> None:
    check, conn = await check_database(_DEAD_DSN)
    assert not check.ok
    assert conn is None
    assert "cannot connect" in check.detail


async def test_migrations_report_applied_versions_after_bootstrap() -> None:
    async with build_app():
        pass
    conn = await asyncpg.connect(_test_dsn())
    try:
        check = await check_migrations(conn, migrations_dir())
    finally:
        await conn.close()
    assert check.ok, check.detail
    assert "applied" in check.detail


async def test_migrations_flag_a_version_the_database_has_not_seen(tmp_path: Path) -> None:
    """An image newer than its database is a real deployment state: the
    worker applies migrations at startup, so a pending one means startup
    did not finish."""
    async with build_app():
        pass
    for sql in sorted(migrations_dir().glob("*.sql")):
        (tmp_path / sql.name).write_text(sql.read_text())
    (tmp_path / "9999_from_a_newer_image.sql").write_text("SELECT 1;")

    conn = await asyncpg.connect(_test_dsn())
    try:
        check = await check_migrations(conn, tmp_path)
    finally:
        await conn.close()
    assert not check.ok
    assert "9999_from_a_newer_image" in check.detail


async def test_migrations_without_any_files_is_a_failure(tmp_path: Path) -> None:
    conn = await asyncpg.connect(_test_dsn())
    try:
        check = await check_migrations(conn, tmp_path)
    finally:
        await conn.close()
    assert not check.ok
    assert "no migrations found" in check.detail


async def test_migrations_on_a_database_with_no_schema_migration_table() -> None:
    """The state a database is in before anything has ever migrated it.

    Staged inside a transaction that is always rolled back: this suite runs
    under xdist against a per-worker database, and dropping the table for
    real would leave every test scheduled after this one on the same worker
    looking at a half-migrated schema.
    """
    conn = await asyncpg.connect(_test_dsn())
    try:
        tx = conn.transaction()
        await tx.start()
        try:
            await conn.execute("DROP TABLE IF EXISTS schema_migration")
            check = await check_migrations(conn, migrations_dir())
        finally:
            await tx.rollback()
    finally:
        await conn.close()
    assert not check.ok
    assert "unreadable" in check.detail


async def test_full_preflight_against_a_live_database(tmp_path: Path) -> None:
    async with build_app():
        pass
    checks = await run_cluster_preflight(
        dsn=_test_dsn(),
        workspace=tmp_path,
        migrations_dir=migrations_dir(),
        environ={},
        uid=10001,
        which=lambda _binary: None,
    )
    assert all_ok(checks), [c for c in checks if not c.ok]
    assert {c.name for c in checks} == {
        "dsn-host",
        "non-root",
        "workspace-writable",
        "engine-auth",
        "database",
        "migrations",
    }


async def test_preflight_skips_the_migration_check_when_the_database_is_unreachable(
    tmp_path: Path,
) -> None:
    """No connection means no migration verdict -- reporting one anyway
    would be inventing a fact about a database nobody reached."""
    checks = await run_cluster_preflight(
        dsn=_DEAD_DSN,
        workspace=tmp_path,
        migrations_dir=migrations_dir(),
        environ={},
        uid=10001,
        which=lambda _binary: None,
    )
    assert not all_ok(checks)
    assert "migrations" not in {c.name for c in checks}


def test_all_ok_is_false_when_any_check_failed() -> None:
    assert all_ok([ClusterCheck("a", True), ClusterCheck("b", True)])
    assert not all_ok([ClusterCheck("a", True), ClusterCheck("b", False)])
