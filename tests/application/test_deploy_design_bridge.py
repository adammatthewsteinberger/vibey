# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""DeployDesignBridgeHandler: the deploy.design kind's production owner."""

from dataclasses import replace
from uuid import uuid4

from tests.application.fakes import FakeJobRepository, make_job
from vibey.application.deploy_design_bridge import DeployDesignBridgeHandler
from vibey.application.worker import Failure, Success
from vibey.domain.job import FailureClass
from vibey.domain.phase import Phase


class FakeTransitioner:
    def __init__(self, *, raises: bool = False) -> None:
        self.calls: list[tuple[object, object]] = []
        self._raises = raises

    async def transition(self, project_id, *, expected, to, cycle=None):  # type: ignore[no-untyped-def]
        self.calls.append((expected, to))
        if self._raises:
            raise ValueError("not in expected phase")


def _job():  # type: ignore[no-untyped-def]
    return replace(make_job(uuid4()), kind="deploy.design", phase=Phase.DEPLOY)


async def test_rejects_wrong_kind() -> None:
    handler = DeployDesignBridgeHandler(jobs=FakeJobRepository(), projects=FakeTransitioner())

    outcome = await handler.handle(replace(_job(), kind="deploy.interview"))

    assert outcome == Failure(FailureClass.VIBEY, "expected deploy.design job")


async def test_bridges_legacy_deploy_phase_and_enqueues_interview() -> None:
    jobs = FakeJobRepository()
    projects = FakeTransitioner()
    handler = DeployDesignBridgeHandler(jobs=jobs, projects=projects)

    outcome = await handler.handle(_job())

    assert isinstance(outcome, Success)
    assert projects.calls == [("deploy", "deploy_design")]
    interviews = [j for j in jobs._jobs.values() if j.kind == "deploy.interview"]
    assert len(interviews) == 1
    assert interviews[0].phase is Phase.DEPLOY_DESIGN


async def test_cas_miss_still_enqueues_the_interview() -> None:
    jobs = FakeJobRepository()
    handler = DeployDesignBridgeHandler(jobs=jobs, projects=FakeTransitioner(raises=True))

    outcome = await handler.handle(_job())

    assert isinstance(outcome, Success)
    assert any(j.kind == "deploy.interview" for j in jobs._jobs.values())


async def test_projects_without_transition_attr_is_skipped() -> None:
    jobs = FakeJobRepository()
    handler = DeployDesignBridgeHandler(jobs=jobs, projects=object())

    outcome = await handler.handle(_job())

    assert isinstance(outcome, Success)
    assert any(j.kind == "deploy.interview" for j in jobs._jobs.values())
