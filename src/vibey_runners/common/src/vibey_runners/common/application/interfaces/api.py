# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The generated REST surface seam."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ApiGateway(Protocol):
    """Opaque vendor HTTP operations, keyed by method path.

    Each runner binds this to its own generated REST client (see that
    runner's own `docs/architecture/decisions/` for its generation and
    drift-guard story); the application layer never depends on the
    generated types directly.
    """

    def invoke(self, method_path: str, **kwargs: object) -> object: ...
