# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

from cursorloop.domain.model_profile import SHIPPED_PRESETS
from cursorloop.infrastructure.agent.bridge import LiveBridge, open_live_bridge


def test_open_live_bridge_creates_agent_with_injected_launcher(tmp_path: Path) -> None:
    calls: dict[str, object] = {}
    os.environ.pop("CURSOR_API_KEY", None)

    def launch_bridge(**kwargs: object) -> SimpleNamespace:
        calls["launch"] = kwargs
        calls["env_during_launch"] = os.environ.get("CURSOR_API_KEY")
        return SimpleNamespace(closed=False, close=lambda: calls.__setitem__("closed", True))

    def create_agent(*, options: object, client: object, **kwargs: object) -> SimpleNamespace:
        del kwargs
        calls["create"] = {"options": options, "client": client}
        return SimpleNamespace(agent_id="agent-1", close=lambda: None)

    bridge = open_live_bridge(
        workspace=tmp_path,
        profile=SHIPPED_PRESETS["composer"],
        api_key="crsr_test",
        launch_bridge=launch_bridge,
        create_agent=create_agent,
    )
    assert isinstance(bridge, LiveBridge)
    assert calls["launch"]["workspace"] == str(tmp_path)
    assert calls["launch"].get("allow_api_key_env_fallback") is True
    assert calls["env_during_launch"] == "crsr_test"
    assert os.environ.get("CURSOR_API_KEY") == "crsr_test"
    assert calls["create"]["client"] is bridge.client
    bridge.close()
    assert calls.get("closed") is True
    assert "CURSOR_API_KEY" not in os.environ


def test_open_live_bridge_resumes_when_agent_id_set(tmp_path: Path) -> None:
    def launch_bridge(**kwargs: object) -> SimpleNamespace:
        del kwargs
        return SimpleNamespace(close=lambda: None)

    def resume_agent(
        agent_id: str, *, options: object, client: object, **kwargs: object
    ) -> SimpleNamespace:
        del options, client, kwargs
        return SimpleNamespace(agent_id=agent_id, close=lambda: None)

    bridge = open_live_bridge(
        workspace=tmp_path,
        profile=SHIPPED_PRESETS["composer"],
        resume_agent_id="bc-123",
        launch_bridge=launch_bridge,
        resume_agent=resume_agent,
        create_agent=lambda **kwargs: (_ for _ in ()).throw(AssertionError("create")),
    )
    assert bridge.agent.agent_id == "bc-123"
    bridge.close()
