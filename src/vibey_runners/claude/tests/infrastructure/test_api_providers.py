# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Tests for infrastructure/api/providers.py — provider factories and surface roots."""

from __future__ import annotations

import pytest

from claudeloop.infrastructure.api.providers import (
    FULL_TREE_PROVIDERS,
    LIMITED_TREE_PROVIDERS,
    PROVIDER_FACTORIES,
    build_client,
    surface_roots_for_provider,
)


class TestProviderFactories:
    def test_all_providers_present(self) -> None:
        expected = {
            "first-party",
            "aws",
            "google-cloud",
            "foundry",
            "bedrock",
            "bedrock-mantle",
            "vertex",
        }
        assert set(PROVIDER_FACTORIES.keys()) == expected

    def test_full_tree_providers(self) -> None:
        assert "first-party" in FULL_TREE_PROVIDERS
        assert "aws" in FULL_TREE_PROVIDERS

    def test_limited_tree_providers(self) -> None:
        assert "bedrock" in LIMITED_TREE_PROVIDERS
        assert "vertex" in LIMITED_TREE_PROVIDERS


class TestBuildClient:
    def test_unknown_provider_raises(self) -> None:
        with pytest.raises(ValueError, match="unknown provider"):
            build_client("nonexistent")

    def test_first_party_returns_client(self, monkeypatch) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-fake-key")
        client = build_client("first-party")
        assert client is not None


class TestSurfaceRootsForProvider:
    def test_full_tree(self) -> None:
        roots = surface_roots_for_provider("first-party")
        assert "messages" in roots
        assert "models" in roots

    def test_limited_tree(self) -> None:
        roots = surface_roots_for_provider("bedrock")
        assert "messages" in roots
        assert "models" not in roots

    def test_unknown_raises(self) -> None:
        with pytest.raises(ValueError, match="unknown provider"):
            surface_roots_for_provider("bogus")
