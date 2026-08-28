# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""run_and_record's optional exit-code channel."""

from collections.abc import AsyncIterator
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

from tests.application.fakes import make_job
from vibey.application.build_engine_run import run_and_record
from vibey.application.dto import EngineEvent, RunHandle
from vibey.infrastructure.engines.descriptors import CLAUDELOOP


class _NoExitCodeEngine:
    """An adapter without the optional run_exit_code capability."""

    descriptor = CLAUDELOOP

    async def tail(self, handle: RunHandle) -> AsyncIterator[EngineEvent]:
        return
        yield  # pragma: no cover


class _NullLedger:
    async def record(self, **kwargs: object) -> None:
        raise AssertionError("no events to record")


def _handle() -> RunHandle:
    return RunHandle(
        run_id=uuid4(),
        engine_id=CLAUDELOOP.engine_id,
        run_dir=Path("/tmp/unused"),
        pid=None,
    )


async def test_adapter_without_the_capability_reports_no_exit_code() -> None:
    job = replace(make_job(uuid4()), kind="build.implement")

    outcome = await run_and_record(
        _NoExitCodeEngine(),  # type: ignore[arg-type]
        _NullLedger(),
        job=job,
        handle=_handle(),
    )

    assert outcome.exit_code is None
    assert not outcome.complete
    assert not outcome.capacity_rejected
