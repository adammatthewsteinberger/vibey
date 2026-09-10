# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from cursorloop.domain.model_profile import SHIPPED_PRESETS
from cursorloop.infrastructure.agent.models import CursorModelCatalog, resolve_profile
from cursorloop.infrastructure.agent.usage import CursorUsageReader
from tests.fixtures import sdk_payloads


def test_unknown_model_is_rejected_against_the_live_catalog_not_a_constant() -> None:
    """Cursor ships models faster than we ship releases, so the catalog is the
    source of truth and the error lists what IS available."""
    catalog = sdk_payloads.fake_model_catalog(["composer-2.5", "cursor-grok-4.6"])
    with pytest.raises(ValueError, match="composer-2.5"):
        resolve_profile("gpt-9-turbo", catalog=catalog)


def test_router_requires_optimize_for_to_be_available_in_the_catalog() -> None:
    catalog = sdk_payloads.fake_model_catalog(["composer-2.5"])  # no auto-smart
    with pytest.raises(ValueError, match="Router"):
        resolve_profile("router-balanced", catalog=catalog)


def test_shipped_preset_resolves_when_its_id_is_in_the_catalog() -> None:
    catalog = sdk_payloads.fake_model_catalog(["composer-2.5", "cursor-grok-4.6"])
    assert resolve_profile("composer", catalog=catalog) == SHIPPED_PRESETS["composer"]
    grok = resolve_profile("grok", catalog=catalog)
    assert grok == SHIPPED_PRESETS["grok"]
    assert grok.effort == "high"


def test_raw_catalog_id_resolves_to_a_profile() -> None:
    catalog = sdk_payloads.fake_model_catalog(["composer-2.5", "some-future-model"])
    profile = resolve_profile("some-future-model", catalog=catalog)
    assert profile.model_id == "some-future-model"


def test_router_preset_resolves_when_auto_smart_is_in_the_catalog() -> None:
    catalog = sdk_payloads.fake_model_catalog(["auto-smart", "composer-2.5"])
    profile = resolve_profile("router-balanced", catalog=catalog)
    assert profile == SHIPPED_PRESETS["router-balanced"]


def test_shipped_preset_is_rejected_when_its_id_is_missing_from_the_catalog() -> None:
    catalog = sdk_payloads.fake_model_catalog(["cursor-grok-4.6"])
    with pytest.raises(ValueError, match="cursor-grok-4.6"):
        resolve_profile("composer", catalog=catalog)


def test_model_catalog_list_all_returns_ids_never_sdk_types() -> None:
    client = SimpleNamespace(
        models=SimpleNamespace(
            list=lambda: (
                SimpleNamespace(id="composer-2.5"),
                SimpleNamespace(id="cursor-grok-4.6"),
            )
        )
    )
    ids = CursorModelCatalog(client).list_all()
    assert ids == ["composer-2.5", "cursor-grok-4.6"]
    assert all(isinstance(item, str) for item in ids)


def test_model_catalog_falls_back_to_client_list_models() -> None:
    client = SimpleNamespace(list_models=lambda: (SimpleNamespace(id="composer-2.5"),))
    assert CursorModelCatalog(client).list_all() == ["composer-2.5"]


def test_model_catalog_is_empty_when_the_client_has_no_list() -> None:
    assert CursorModelCatalog(SimpleNamespace()).list_all() == []


def test_resolve_profile_accepts_a_model_catalog_port() -> None:
    catalog = CursorModelCatalog(
        SimpleNamespace(models=SimpleNamespace(list=lambda: (SimpleNamespace(id="composer-2.5"),)))
    )
    assert resolve_profile("composer-2.5", catalog=catalog).model_id == "composer-2.5"


@dataclass
class _FakeUsageCost:
    raw_cost_cents: float
    charged_cents: float


@dataclass
class _FakeAgentUsage:
    usage: sdk_payloads.FakeTokenUsage
    runs: tuple[object, ...] = ()
    cost: object | None = None


class _FakeUsageAgent:
    def __init__(self, usage: _FakeAgentUsage) -> None:
        self._usage = usage

    def get_usage(self, *, run_id: str | None = None) -> _FakeAgentUsage:
        del run_id
        return self._usage


async def test_billed_cost_usd_is_none_when_cost_has_not_settled() -> None:
    """billed_cost_usd returns None (never 0.0) when AgentUsage.cost is None."""
    agent = _FakeUsageAgent(
        _FakeAgentUsage(usage=sdk_payloads.FakeTokenUsage(total_tokens=9), cost=None)
    )
    reader = CursorUsageReader(agent)
    assert await reader.billed_cost_usd() is None
    assert await reader.turn_tokens("run_1") == 9


async def test_billed_cost_usd_converts_charged_cents() -> None:
    agent = _FakeUsageAgent(
        _FakeAgentUsage(
            usage=sdk_payloads.FakeTokenUsage(total_tokens=4),
            cost=_FakeUsageCost(raw_cost_cents=200.0, charged_cents=125.0),
        )
    )
    reader = CursorUsageReader(agent)
    assert await reader.billed_cost_usd() == 1.25


async def test_billed_cost_usd_is_none_when_charged_cents_is_missing() -> None:
    agent = _FakeUsageAgent(
        _FakeAgentUsage(
            usage=sdk_payloads.FakeTokenUsage(total_tokens=1),
            cost=SimpleNamespace(raw_cost_cents=10.0, charged_cents=None),
        )
    )
    assert await CursorUsageReader(agent).billed_cost_usd() is None


async def test_turn_tokens_prefer_the_matching_run_breakdown() -> None:
    run_usage = SimpleNamespace(run_id="run_9", usage=sdk_payloads.FakeTokenUsage(total_tokens=42))
    agent = _FakeUsageAgent(
        _FakeAgentUsage(
            usage=sdk_payloads.FakeTokenUsage(total_tokens=99),
            runs=(run_usage,),
            cost=None,
        )
    )
    reader = CursorUsageReader(agent)
    assert await reader.turn_tokens("run_9") == 42
    assert await reader.turn_tokens("missing") == 99
