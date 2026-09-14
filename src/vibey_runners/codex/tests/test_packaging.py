# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Packaging contract: version, typing marker, and installable metadata."""

from __future__ import annotations

from pathlib import Path

from packaging.version import Version

_ROOT = Path(__file__).resolve().parents[1]


def test_dunder_version_is_pep_440() -> None:
    import codexloop

    Version(codexloop.__version__)


def test_py_typed_marker_exists() -> None:
    marker = _ROOT / "src" / "codexloop" / "py.typed"
    assert marker.is_file(), f"expected PEP 561 marker at {marker}"


def test_installed_distribution_version_resolves() -> None:
    from importlib.metadata import version

    import codexloop

    assert version("codexloop") == codexloop.__version__
