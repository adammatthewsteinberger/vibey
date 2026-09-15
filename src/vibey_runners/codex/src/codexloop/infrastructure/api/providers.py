# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Alternate OpenAI SDK client selection for ``codexloop api --provider``."""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

from openai import AzureOpenAI, OpenAI

ProviderFactory = Callable[..., Any]

# Keys exposed on the CLI (--provider values use kebab-case via Typer).
PROVIDER_FACTORIES: dict[str, ProviderFactory] = {
    "openai": lambda **kwargs: OpenAI(**kwargs),
    "azure": lambda **kwargs: AzureOpenAI(**kwargs),
    "custom": lambda **kwargs: OpenAI(**kwargs),
}

FULL_TREE_PROVIDERS = frozenset({"openai", "custom"})
# AzureOpenAI subclasses OpenAI, so the class tree is the same; keep the set
# explicit so a future limited Azure surface can shrink without surprise.
AZURE_TREE_PROVIDERS = frozenset({"azure"})


def build_client(provider: str, *, base_url: str | None = None) -> Any:
    factory = PROVIDER_FACTORIES.get(provider)
    if factory is None:
        known = ", ".join(sorted(PROVIDER_FACTORIES))
        msg = f"unknown provider {provider!r}; expected one of: {known}"
        raise ValueError(msg)
    kwargs: dict[str, Any] = {}
    if base_url is not None:
        kwargs["base_url"] = base_url
    elif provider == "custom":
        env_url = os.environ.get("OPENAI_BASE_URL")
        if env_url:
            kwargs["base_url"] = env_url
    if provider == "azure":
        # AzureOpenAI requires api_version; allow env defaults used by the SDK.
        if "api_version" not in kwargs and os.environ.get("OPENAI_API_VERSION"):
            kwargs["api_version"] = os.environ["OPENAI_API_VERSION"]
        # Dummy key only when constructing for help/introspection paths that
        # never call the network — real invokes still need credentials.
        if not os.environ.get("AZURE_OPENAI_API_KEY") and not os.environ.get("OPENAI_API_KEY"):
            kwargs.setdefault("api_key", "codexloop-azure-placeholder")
        if not os.environ.get("AZURE_OPENAI_ENDPOINT") and "azure_endpoint" not in kwargs:
            kwargs.setdefault("azure_endpoint", "https://example.openai.azure.com")
        if "api_version" not in kwargs:
            kwargs.setdefault("api_version", "2024-02-01")
    elif not os.environ.get("OPENAI_API_KEY"):
        kwargs.setdefault("api_key", "codexloop-placeholder")
    return factory(**kwargs)


def client_class_for_provider(provider: str) -> type:
    if provider == "azure":
        return AzureOpenAI
    if provider in {"openai", "custom"}:
        return OpenAI
    msg = f"unknown provider {provider!r}"
    raise ValueError(msg)


def surface_roots_for_provider(provider: str) -> tuple[str, ...] | None:
    """Return restricted roots, or ``None`` for the full OpenAI tree."""
    if provider in FULL_TREE_PROVIDERS or provider in AZURE_TREE_PROVIDERS:
        return None
    msg = f"unknown provider {provider!r}"
    raise ValueError(msg)
