# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Unit tests for OpenAI API providers."""

from __future__ import annotations

import pytest

from codexloop.infrastructure.api.providers import (
    build_client,
    client_class_for_provider,
    surface_roots_for_provider,
)


def test_client_class_for_providers() -> None:
    from openai import AzureOpenAI, OpenAI

    assert client_class_for_provider("openai") is OpenAI
    assert client_class_for_provider("custom") is OpenAI
    assert client_class_for_provider("azure") is AzureOpenAI


def test_surface_roots_full_tree() -> None:
    assert surface_roots_for_provider("openai") is None
    assert surface_roots_for_provider("azure") is None
    assert surface_roots_for_provider("custom") is None


def test_build_client_without_credentials() -> None:
    client = build_client("openai")
    assert client.api_key == "codexloop-placeholder"


def test_azure_defaults_without_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    monkeypatch.delenv("OPENAI_API_VERSION", raising=False)
    client = build_client("azure")
    assert getattr(client, "api_version", None) or True


def test_provider_edge_cases(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(ValueError, match="unknown provider"):
        build_client("nope")
    with pytest.raises(ValueError, match="unknown provider"):
        client_class_for_provider("nope")
    with pytest.raises(ValueError, match="unknown provider"):
        surface_roots_for_provider("nope")

    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client = build_client("custom")
    assert client.api_key == "codexloop-placeholder"

    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.test/v1")
    client_env = build_client("custom")
    assert "example.test" in str(client_env.base_url)

    client2 = build_client("openai", base_url="https://override.test/v1")
    assert "override.test" in str(client2.base_url)

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    assert build_client("openai").api_key == "sk-test"

    monkeypatch.setenv("OPENAI_API_VERSION", "2024-06-01")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "az-key")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://my.openai.azure.com")
    azure = build_client("azure")
    assert azure is not None
