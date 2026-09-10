# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The generated REST surface seam."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ApiGateway(Protocol):
    """Generated Gemini REST surface (ADR 0015). ``agyloop api`` is bound from
    the committed Developer discovery baseline and guarded by a drift gate."""

    def invoke(self, method_path: str, **kwargs: Any) -> Any: ...
