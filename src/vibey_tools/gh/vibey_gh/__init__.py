# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""GitHub automation and provenance fingerprints, installable into any repository.

This package carries the release automation that vibey projects share — the merge train,
the promotion train, branch-driven publishing, derived version bumps — and the fingerprint
rule that says every code change is attributable.

It is deliberately CONFIG-DRIVEN rather than hard-coded. What counts as packaged content,
which files hold the version, which branches are integration and release, and the
fingerprint text itself all come from a `.vibey-gh.toml` in the consuming repository, so
the same code serves a plugin marketplace, a Python library, or anything else.

Consuming repositories do not vendor copies. They depend on this package as DEV tooling
and call it, so there is one implementation to fix rather than one per repo. That also
keeps a consumer's runtime dependency list empty, which matters when its release pipeline
verifies an artifact against a single index.
"""

from vibey_gh.config import GhConfig, load_config

__version__ = "1.73.0"

__all__ = ["GhConfig", "__version__", "load_config"]
