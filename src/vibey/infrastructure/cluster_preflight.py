# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""In-cluster preflight: the wiring checks a deployed worker cannot make
for itself, but which decide whether it will work at all.

Every check here corresponds to a way a chart install has actually failed
or could silently half-work. A worker that starts, logs "worker started",
and reports Ready can still be unable to create a worktree, unable to
authenticate any engine, or wired to a DSN that its own autoscaler cannot
resolve. None of those surface as a crash; they surface as work that
never gets done.
"""

import ipaddress
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

import asyncpg

from vibey.domain.engine import EngineId
from vibey.infrastructure.db.migrator import discover_migrations
from vibey.infrastructure.engines.descriptors import ALL_DESCRIPTORS


@dataclass(frozen=True, slots=True)
class ClusterCheck:
    name: str
    ok: bool
    detail: str = ""


# Subscription login is a TTY flow and does not exist in a cluster, so an
# engine in a container authenticates by API key or not at all. These are
# the variables each runner's own doctor_env looks for.
ENGINE_API_KEY_ENVS: Mapping[EngineId, tuple[str, ...]] = {
    EngineId.CLAUDELOOP: ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN"),
    EngineId.CODEXLOOP: ("OPENAI_API_KEY", "AZURE_OPENAI_API_KEY", "CODEX_API_KEY"),
    EngineId.CURSORLOOP: ("CURSOR_API_KEY",),
    EngineId.AGYLOOP: ("GOOGLE_API_KEY", "GEMINI_API_KEY", "GOOGLE_APPLICATION_CREDENTIALS"),
}

_ALWAYS_RESOLVABLE = frozenset({"localhost"})


def _resolves_beyond_namespace(host: str) -> bool:
    if host in _ALWAYS_RESOLVABLE:
        return True
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return "." in host
    return True


def check_dsn_resolves_cluster_wide(dsn: str) -> ClusterCheck:
    """A bare Service name resolves only from inside its own namespace.

    The worker is in that namespace, so it never notices. KEDA's operator
    is not: it dials Postgres itself to evaluate the scaler query, and an
    unqualified DSN fails there and nowhere else. That is exactly how one
    shipped once.
    """
    host = urlsplit(dsn).hostname
    if host is None:
        return ClusterCheck("dsn-host", False, "DSN has no host component")
    if _resolves_beyond_namespace(host):
        return ClusterCheck("dsn-host", True, host)
    return ClusterCheck(
        "dsn-host",
        False,
        f"{host!r} is a bare name -- it resolves only inside this namespace. "
        "Readers outside it (KEDA's operator, notably) cannot. "
        "Use <service>.<namespace>.svc.<clusterDomain>.",
    )


def check_not_root(uid: int) -> ClusterCheck:
    """The chart runs the pod as uid 10001 with allowPrivilegeEscalation
    false. Running as root means that security context was lost."""
    if uid == 0:
        return ClusterCheck("non-root", False, "running as root (uid 0)")
    return ClusterCheck("non-root", True, f"uid {uid}")


def check_workspace_writable(workspace: Path) -> ClusterCheck:
    """BUILD phase work happens in real git worktrees the worker creates
    itself. A read-only or wrongly-owned volume fails at the first one,
    long after the pod reports Ready."""
    probe = workspace / ".vibey-preflight"
    try:
        probe.write_text("ok")
        probe.unlink()
    except OSError as exc:
        return ClusterCheck("workspace-writable", False, f"{workspace}: {exc}")
    return ClusterCheck("workspace-writable", True, str(workspace))


def check_engine_auth(
    environ: Mapping[str, str],
    *,
    which: Callable[[str], str | None],
) -> ClusterCheck:
    """An engine binary present with no credentials is the misconfiguration
    worth catching. No binaries at all is the scripted-only image, which is
    a deliberate state today, not a fault."""
    installed = [d for d in ALL_DESCRIPTORS if which(d.binary) is not None]
    if not installed:
        return ClusterCheck(
            "engine-auth", True, "no engine binaries installed (scripted-provider image)"
        )
    unauthenticated = [
        d.engine_id.value
        for d in installed
        if not any(environ.get(var) for var in ENGINE_API_KEY_ENVS[d.engine_id])
    ]
    if unauthenticated:
        return ClusterCheck(
            "engine-auth",
            False,
            f"installed but unauthenticated: {', '.join(sorted(unauthenticated))} "
            "-- subscription login does not exist in a cluster; mount API keys as a Secret",
        )
    return ClusterCheck("engine-auth", True, f"{len(installed)} engine(s) authenticated by API key")


async def check_database(dsn: str) -> tuple[ClusterCheck, asyncpg.Connection | None]:
    try:
        conn: asyncpg.Connection = await asyncpg.connect(dsn)
    except (OSError, asyncpg.PostgresError) as exc:
        return ClusterCheck("database", False, f"cannot connect: {exc}"), None
    return ClusterCheck("database", True, "connected"), conn


async def check_migrations(conn: asyncpg.Connection, migrations_dir: Path) -> ClusterCheck:
    """The worker applies migrations at startup, so a pending migration
    here means startup did not finish or the image is older than the
    database expects."""
    expected = {m.version for m in discover_migrations(migrations_dir)}
    if not expected:
        return ClusterCheck("migrations", False, f"no migrations found at {migrations_dir}")
    try:
        rows = await conn.fetch("SELECT version FROM schema_migration")
    except asyncpg.PostgresError as exc:
        return ClusterCheck("migrations", False, f"schema_migration unreadable: {exc}")
    applied = {str(r["version"]) for r in rows}
    pending = sorted(expected - applied)
    if pending:
        return ClusterCheck("migrations", False, f"pending: {', '.join(pending)}")
    return ClusterCheck("migrations", True, f"{len(applied)} applied")


async def run_cluster_preflight(
    *,
    dsn: str,
    workspace: Path,
    migrations_dir: Path,
    environ: Mapping[str, str],
    uid: int,
    which: Callable[[str], str | None],
) -> tuple[ClusterCheck, ...]:
    checks: list[ClusterCheck] = [
        check_dsn_resolves_cluster_wide(dsn),
        check_not_root(uid),
        check_workspace_writable(workspace),
        check_engine_auth(environ, which=which),
    ]
    db_check, conn = await check_database(dsn)
    checks.append(db_check)
    if conn is not None:
        try:
            checks.append(await check_migrations(conn, migrations_dir))
        finally:
            await conn.close()
    return tuple(checks)


def all_ok(checks: Sequence[ClusterCheck]) -> bool:
    return all(c.ok for c in checks)
