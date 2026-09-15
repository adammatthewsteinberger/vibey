# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Resolve model profiles against the live vendor catalog, never a constant."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from cursorloop.domain.model_profile import SHIPPED_PRESETS, ModelProfile

_ROUTER_ID = "auto-smart"


def _catalog_ids(catalog: Sequence[str] | Any) -> list[str]:
    list_all = getattr(catalog, "list_all", None)
    if callable(list_all):
        return [str(item) for item in list_all()]
    return [str(item) for item in catalog]


def resolve_profile(name: str, *, catalog: Sequence[str] | Any) -> ModelProfile:
    """Look up a shipped preset or raw model id against the live catalog.

    Unknown ids are rejected with a message that lists what IS available.
    Router presets additionally require ``auto-smart`` in the catalog.
    """
    ids = _catalog_ids(catalog)
    available = ", ".join(ids)
    if name in SHIPPED_PRESETS:
        profile = SHIPPED_PRESETS[name]
        if profile.model_id not in ids:
            if profile.model_id == _ROUTER_ID:
                raise ValueError(
                    f"Router profile {name!r} requires {_ROUTER_ID!r} in the catalog; "
                    f"available: {available}"
                )
            raise ValueError(f"Unknown model {name!r}. Available: {available}")
        return profile
    if name not in ids:
        raise ValueError(f"Unknown model {name!r}. Available: {available}")
    return ModelProfile(model_id=name)


class CursorModelCatalog:
    """``ModelCatalog`` over ``client.models.list()``. Returns ids, never SDK types."""

    def __init__(self, client: Any) -> None:
        self._client = client

    def list_all(self) -> list[str]:
        models_ns = getattr(self._client, "models", None)
        list_fn: Callable[..., Any] | None = getattr(models_ns, "list", None)
        if not callable(list_fn):
            list_fn = getattr(self._client, "list_models", None)
        if not callable(list_fn):
            return []
        models = list_fn()
        ids: list[str] = []
        for model in models:
            mid = getattr(model, "id", model)
            if isinstance(mid, str):
                ids.append(mid)
        return ids
