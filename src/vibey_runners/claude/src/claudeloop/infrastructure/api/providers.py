# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Alternate Anthropic SDK client selection for ``claudeloop api --provider``."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from anthropic import (
    Anthropic,
    AnthropicAWS,
    AnthropicBedrock,
    AnthropicBedrockMantle,
    AnthropicFoundry,
    AnthropicGoogleCloud,
    AnthropicVertex,
)

ProviderFactory = Callable[..., Any]

# Keys exposed on the CLI (--provider values use kebab-case via Typer).
PROVIDER_FACTORIES: dict[str, ProviderFactory] = {
    "first-party": lambda: Anthropic(),
    "aws": lambda: AnthropicAWS(),
    "google-cloud": lambda: AnthropicGoogleCloud(),
    "foundry": lambda: AnthropicFoundry(),
    "bedrock": lambda: AnthropicBedrock(),
    "bedrock-mantle": lambda: AnthropicBedrockMantle(),
    "vertex": lambda: AnthropicVertex(),
}

FULL_TREE_PROVIDERS = frozenset({"first-party", "aws", "google-cloud", "foundry"})
LIMITED_TREE_PROVIDERS = frozenset({"bedrock", "bedrock-mantle", "vertex"})


def build_client(provider: str) -> Any:
    factory = PROVIDER_FACTORIES.get(provider)
    if factory is None:
        known = ", ".join(sorted(PROVIDER_FACTORIES))
        msg = f"unknown provider {provider!r}; expected one of: {known}"
        raise ValueError(msg)
    return factory()


def surface_roots_for_provider(provider: str) -> tuple[str, ...]:
    if provider in FULL_TREE_PROVIDERS:
        return ("messages", "models", "beta")
    if provider in LIMITED_TREE_PROVIDERS:
        return ("messages", "beta")
    msg = f"unknown provider {provider!r}"
    raise ValueError(msg)
