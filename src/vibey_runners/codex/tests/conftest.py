# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Shared pytest fixtures. The fake `codex` PATH shim is opt-in, not autouse."""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path

import pytest

_SHIM = Path(__file__).resolve().parent / "shim" / "fake_codex.py"


def configure_fake_codex(
    monkeypatch: pytest.MonkeyPatch,
    *,
    script: Path | str | None = None,
    mode: str = "stream",
) -> None:
    """Set FAKE_CODEX_SCRIPT and FAKE_CODEX_MODE for the shim."""
    monkeypatch.setenv("FAKE_CODEX_MODE", mode)
    if script is None:
        monkeypatch.delenv("FAKE_CODEX_SCRIPT", raising=False)
    else:
        monkeypatch.setenv("FAKE_CODEX_SCRIPT", str(script))


@pytest.fixture
def fake_codex_on_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Prepend a tmp bin dir containing an executable `codex` that runs the shim."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    dest = bin_dir / "codex"
    dest.write_text(
        "#!/usr/bin/env python3\n"
        "import runpy\n"
        f"runpy.run_path({str(_SHIM)!r}, run_name='__main__')\n",
        encoding="utf-8",
    )
    dest.chmod(0o755)
    monkeypatch.setenv("PATH", os.pathsep.join((str(bin_dir), os.environ.get("PATH", ""))))
    return bin_dir


@pytest.fixture(name="configure_fake_codex")
def configure_fake_codex_fixture(
    monkeypatch: pytest.MonkeyPatch,
) -> Callable[..., None]:
    def _configure(*, script: Path | str | None = None, mode: str = "stream") -> None:
        configure_fake_codex(monkeypatch, script=script, mode=mode)

    return _configure
