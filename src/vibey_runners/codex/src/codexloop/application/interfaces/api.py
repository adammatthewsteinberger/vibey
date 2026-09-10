# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The generated REST surface seam."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ApiGateway(Protocol):
    def invoke(self, method_path: str, **kwargs: object) -> object: ...
