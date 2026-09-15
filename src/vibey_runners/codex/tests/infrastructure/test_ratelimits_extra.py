# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Coverage for app-server rate-limit mapping helpers."""

from __future__ import annotations

from datetime import UTC, datetime

from codexloop.infrastructure.appserver.ratelimits import plan_windows_from_rpc


def test_plan_windows_from_nested_and_flat() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    nested = {
        "payload": {
            "rate_limits": {
                "plan_type": "plus",
                "rate_limit_reached_type": None,
                "primary": {
                    "used_percent": 10.5,
                    "window_minutes": 60,
                    "resets_in_seconds": 30,
                },
                "secondary": {
                    "used_percent": 1,
                    "window_minutes": 10080,
                    "resets_at": now.timestamp() + 100,
                },
            }
        }
    }
    windows = plan_windows_from_rpc(nested, now=now)
    assert windows is not None
    assert windows.plan_type == "plus"
    assert windows.primary is not None
    assert windows.primary.window_minutes == 60
    assert windows.secondary is not None

    flat = {
        "plan_type": "free",
        "primary": {"window_minutes": 5, "used_percent": 0},
    }
    assert plan_windows_from_rpc(flat, now=now) is not None
    assert plan_windows_from_rpc("nope", now=now) is None
    assert plan_windows_from_rpc({"other": 1}, now=now) is None
    assert plan_windows_from_rpc({"primary": "bad"}, now=now) is not None
