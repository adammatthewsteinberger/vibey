# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Compatibility alias for the standalone `vibey-gh` package.

This subpackage shipped the GitHub automation in 4.1.0. In 4.2.0 the code moved to
[vibey-gh](https://pypi.org/project/vibey-gh/), which has no dependencies, because
release tooling runs in every CI job of every repository that adopts it — and reaching it
through this package meant installing the Azure SDK and OpenTelemetry to run a stdlib CLI.

`vibey-gh` is a hard dependency here, so every import that worked before still works:

    from vibey_bootstrap.gh import merge_train          # the module
    from vibey_bootstrap.gh.config import GhConfig      # and its submodules

Both now resolve to the same objects `vibey_gh` exposes — not copies of them, so patching
one is patching the other. New code should import `vibey_gh` directly.
"""

from __future__ import annotations

import sys

import vibey_gh
from vibey_gh import cli, config, fingerprints, install, merge_train, realign, versioning

# Register the submodules under this package's name too. Without this,
# `from vibey_bootstrap.gh.config import GhConfig` raises ModuleNotFoundError: the names
# above are bound as attributes, but Python's import machinery looks in sys.modules.
for _name, _module in (
    ("cli", cli),
    ("config", config),
    ("fingerprints", fingerprints),
    ("install", install),
    ("merge_train", merge_train),
    ("realign", realign),
    ("versioning", versioning),
):
    sys.modules[f"{__name__}.{_name}"] = _module

__version__ = getattr(vibey_gh, "__version__", "")

__all__ = [
    "cli",
    "config",
    "fingerprints",
    "install",
    "merge_train",
    "realign",
    "versioning",
]
