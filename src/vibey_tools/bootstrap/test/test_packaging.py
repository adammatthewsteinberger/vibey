# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The declared package list is hand-maintained, so something has to check it.

`[tool.setuptools] packages` is an explicit list rather than a `find:` directive, which
is a deliberate choice -- it keeps a new directory from silently entering the
distribution. The cost is the opposite failure, and this repository has already paid it:
`vibey_bootstrap.gh` shipped in 4.1.0, moved to the standalone `vibey-gh` package in
4.2.0 leaving a compatibility shim behind, and the shim was never added to this list. Its
own docstring promises "every import that worked before still works"; for anyone
installing the wheel it raised ModuleNotFoundError instead, and the suite could not see
that because it runs against the source tree.
"""

from __future__ import annotations

import pathlib
import tomllib

REPO = pathlib.Path(__file__).resolve().parent.parent


def _declared() -> set[str]:
    data = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
    return set(data["tool"]["setuptools"]["packages"])


def _on_disk() -> set[str]:
    return {
        ".".join(path.parent.relative_to(REPO).parts)
        for path in (REPO / "vibey_bootstrap").rglob("__init__.py")
    }


def test_every_package_on_disk_is_declared() -> None:
    missing = sorted(_on_disk() - _declared())
    assert not missing, (
        f"these packages exist but would not ship: {missing}. Add them to "
        f"[tool.setuptools] packages in pyproject.toml."
    )


def test_every_declared_package_exists() -> None:
    """The other direction: a stale entry makes the build fail late and obscurely."""
    absent = sorted(_declared() - _on_disk())
    assert not absent, f"declared but not on disk: {absent}"


def test_the_compatibility_shim_is_declared() -> None:
    """Named explicitly, because this is the one the list actually lost."""
    assert "vibey_bootstrap.gh" in _declared()
