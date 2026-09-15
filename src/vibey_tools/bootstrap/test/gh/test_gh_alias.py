# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""`vibey_bootstrap.gh` is an alias for the standalone `vibey-gh` package.

The implementation and its tests moved to that package. What still has to hold HERE is
the compatibility promise 4.1.0 made: every import that worked then works now, and
resolves to the same object rather than a copy — because a copy would mean patching one
and not the other, which is the subtlest way for a shim to be wrong.
"""

from __future__ import annotations

import pytest
import vibey_gh

from vibey_bootstrap import gh

SUBMODULES = ["cli", "config", "fingerprints", "install", "merge_train", "realign", "versioning"]


@pytest.mark.parametrize("name", SUBMODULES)
def test_each_submodule_is_the_very_same_module_object(name):
    import importlib

    assert getattr(gh, name) is getattr(vibey_gh, name)
    # The import machinery reads sys.modules, so attribute binding alone is not enough:
    # `from vibey_bootstrap.gh.config import GhConfig` has to resolve too.
    assert importlib.import_module(f"vibey_bootstrap.gh.{name}") is getattr(vibey_gh, name)


def test_the_names_the_old_package_exported_still_import():
    from vibey_bootstrap.gh.config import GhConfig, load_config, normalise_actor
    from vibey_bootstrap.gh.merge_train import Verdict

    assert GhConfig is vibey_gh.config.GhConfig
    assert load_config is vibey_gh.config.load_config
    assert normalise_actor("app/claude") == "claude"
    assert Verdict(1, "t", "a", None).ready is True


def test_the_alias_reports_the_version_of_the_package_backing_it():
    assert gh.__version__ == vibey_gh.__version__
    assert gh.__version__


def test_patching_through_the_alias_patches_the_real_module(monkeypatch):
    """The property a copy would break."""
    monkeypatch.setattr(gh.versioning, "read_version", lambda cfg: "9.9.9")
    assert vibey_gh.versioning.read_version(None) == "9.9.9"
