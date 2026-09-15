# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Generated Anthropic SDK REST CLI (M4)."""

from __future__ import annotations

from claudeloop.infrastructure.api.binder import build_api_click_group
from claudeloop.infrastructure.api.gateway import AnthropicApiGateway, default_gateway
from claudeloop.infrastructure.api.introspect import (
    LOCAL_HELPER_PATHS,
    SDK_VERSION,
    DiscoveredMethod,
    discover_surface,
    method_by_path,
    resolve_callable,
)

__all__ = [
    "LOCAL_HELPER_PATHS",
    "SDK_VERSION",
    "AnthropicApiGateway",
    "DiscoveredMethod",
    "build_api_click_group",
    "default_gateway",
    "discover_surface",
    "method_by_path",
    "resolve_callable",
]
