# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Use case: probe capacity without spending a real turn."""

from __future__ import annotations

from codexloop.application.dto import ProbeResult
from codexloop.application.runner import RunnerContext


async def preflight(ctx: RunnerContext) -> ProbeResult:
    return await ctx.probe.probe()
