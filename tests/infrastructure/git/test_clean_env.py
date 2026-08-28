# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
import asyncio

import pytest

from vibey.infrastructure.git.clean_env import CleanGitEnvSubprocessExecutor


async def test_cancelled_error_terminates_and_reaps_subprocess(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeProcess:
        returncode = None
        terminated = False
        waited = False

        async def communicate(self) -> tuple[bytes, bytes]:
            raise asyncio.CancelledError

        def terminate(self) -> None:
            FakeProcess.terminated = True

        async def wait(self) -> None:
            FakeProcess.waited = True

    async def fake_create(*args: object, **kwargs: object) -> FakeProcess:
        return FakeProcess()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create)

    with pytest.raises(asyncio.CancelledError):
        await CleanGitEnvSubprocessExecutor().execute(("git", "status"))

    assert FakeProcess.terminated
    assert FakeProcess.waited
