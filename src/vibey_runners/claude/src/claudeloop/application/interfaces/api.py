# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The generated REST surface seam."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ApiGateway(Protocol):
    """Declared now; implemented in M4 alongside the generated REST surface.
    See docs/architecture/decisions/0006-generated-rest-surface-not-hand-written.md."""

    def invoke(self, method_path: str, **kwargs: Any) -> Any: ...
