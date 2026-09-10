# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Generated OpenAI SDK REST CLI (M4)."""

from __future__ import annotations

from codexloop.infrastructure.api.binder import build_api_typer_app
from codexloop.infrastructure.api.gateway import OpenAIApiGateway, default_gateway
from codexloop.infrastructure.api.introspect import (
    LOCAL_HELPER_PATHS,
    SDK_VERSION,
    EndpointSpec,
    discover_surface,
    method_by_path,
    resolve_callable,
)

__all__ = [
    "LOCAL_HELPER_PATHS",
    "SDK_VERSION",
    "EndpointSpec",
    "OpenAIApiGateway",
    "build_api_typer_app",
    "default_gateway",
    "discover_surface",
    "method_by_path",
    "resolve_callable",
]
