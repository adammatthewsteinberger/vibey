"""Alembic migration conventions — env-driven harness."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

ENV_PY_TEMPLATE = '''"""Alembic env.py — reads DATABASE_URL at runtime."""
from logging.config import fileConfig
import os
from alembic import context
from sqlalchemy import engine_from_config, pool

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None
database_url = os.environ.get("DATABASE_URL", "")
config.set_main_option("sqlalchemy.url", database_url)


def run_migrations_offline() -> None:
    context.configure(url=database_url, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''


def upgrade_to_head(*, alembic_ini: str | Path = "alembic.ini") -> None:
    from alembic import command  # type: ignore[import-untyped]
    from alembic.config import Config  # type: ignore[import-untyped]

    cfg = Config(str(alembic_ini))
    command.upgrade(cfg, "head")


def current(*, alembic_ini: str | Path = "alembic.ini") -> str | None:
    import io
    from contextlib import redirect_stdout

    from alembic import command  # type: ignore[import-untyped]
    from alembic.config import Config  # type: ignore[import-untyped]

    cfg = Config(str(alembic_ini))
    buf = io.StringIO()
    with redirect_stdout(buf):
        command.current(cfg)
    return buf.getvalue().strip() or None


def stamp(revision: str, *, alembic_ini: str | Path = "alembic.ini") -> None:
    from alembic import command  # type: ignore[import-untyped]
    from alembic.config import Config  # type: ignore[import-untyped]

    cfg = Config(str(alembic_ini))
    command.stamp(cfg, revision)


def write_env_py(target_dir: str | Path) -> Path:
    """Write the bundled env.py template to *target_dir*."""
    path = Path(target_dir) / "env.py"
    path.write_text(ENV_PY_TEMPLATE, encoding="utf-8")
    return path


__all__ = ["ENV_PY_TEMPLATE", "current", "stamp", "upgrade_to_head", "write_env_py"]
