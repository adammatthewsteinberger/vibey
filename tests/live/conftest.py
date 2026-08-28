# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Fixtures shared by all tests/live/ tests.

Faked mode (marker: @pytest.mark.live) uses ScriptedEngine with real
directory shapes but no subprocess. Paid mode (marker: @pytest.mark.paid)
spawns real engine binaries against real models.
"""

from pathlib import Path

import pytest

from vibey.infrastructure.engines.descriptors import (
    ALL_DESCRIPTORS,
    BY_ENGINE_ID,
)
from vibey.infrastructure.engines.loop_process_adapter import LoopProcessAdapter
from vibey.infrastructure.engines.scripted import ScriptedEngine


@pytest.fixture(params=ALL_DESCRIPTORS, ids=lambda d: d.engine_id.value)
def scripted_engine(request: pytest.FixtureRequest, tmp_path: Path) -> ScriptedEngine:
    return ScriptedEngine(descriptor=request.param, base_dir=tmp_path)


@pytest.fixture(params=ALL_DESCRIPTORS, ids=lambda d: d.engine_id.value)
def live_adapter(request: pytest.FixtureRequest) -> LoopProcessAdapter:
    return LoopProcessAdapter(descriptor=request.param)


@pytest.fixture()
def descriptors_by_id() -> dict:
    return dict(BY_ENGINE_ID)
