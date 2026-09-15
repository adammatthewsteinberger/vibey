"""DB migrations tests."""

from __future__ import annotations

from pathlib import Path

from vibey_bootstrap.db.migrations import ENV_PY_TEMPLATE, write_env_py


def test_write_env_py(tmp_path: Path) -> None:
    path = write_env_py(tmp_path)
    assert path.exists()
    assert "DATABASE_URL" in path.read_text()


def test_env_template_nonempty() -> None:
    assert "run_migrations_online" in ENV_PY_TEMPLATE
