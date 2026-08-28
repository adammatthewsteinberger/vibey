# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Shared fakes for vibey test suites.

Re-exports from application/fakes.py (the original home) plus new
fakes for protocols added in Phase E1.
"""

from tests.application.fakes import FakeHumanGateRepository, FakeJobRepository

__all__ = [
    "FakeEngineHealthRepository",
    "FakeHumanGateRepository",
    "FakeJobRepository",
    "FakeRotationCursorRepository",
]


class FakeEngineHealthRepository:
    """In-memory fake for EngineHealthRepository."""

    def __init__(self) -> None:
        from vibey.application.dto import EngineHealthRecord

        self._records: dict[tuple[object, str], EngineHealthRecord] = {}

    async def get(self, project_id: object, engine_id: str) -> object:
        return self._records.get((project_id, engine_id))

    async def upsert(self, record: object) -> object:
        from vibey.application.dto import EngineHealthRecord

        assert isinstance(record, EngineHealthRecord)
        self._records[(record.project_id, record.engine_id.value)] = record
        return record

    async def list_for_project(self, project_id: object) -> tuple[object, ...]:
        return tuple(r for (pid, _), r in self._records.items() if pid == project_id)


class FakeRotationCursorRepository:
    """In-memory fake for RotationCursorRepository."""

    def __init__(self) -> None:
        from vibey.application.dto import RotationCursor

        self._cursors: dict[tuple[object, str], RotationCursor] = {}

    async def get(self, project_id: object, engine_id: object) -> object:
        from vibey.domain.engine import EngineId

        assert isinstance(engine_id, EngineId)
        return self._cursors.get((project_id, engine_id.value))

    async def list_for_project(self, project_id: object) -> tuple[object, ...]:
        matching = [c for (pid, _), c in self._cursors.items() if pid == project_id]
        return tuple(sorted(matching, key=lambda c: c.order))

    async def upsert(self, cursor: object) -> object:
        from vibey.application.dto import RotationCursor

        assert isinstance(cursor, RotationCursor)
        self._cursors[(cursor.project_id, cursor.engine_id.value)] = cursor
        return cursor

    async def update_many(
        self, project_id: object, cursors: tuple[object, ...]
    ) -> tuple[object, ...]:
        from vibey.application.dto import RotationCursor

        for c in cursors:
            assert isinstance(c, RotationCursor)
            self._cursors[(c.project_id, c.engine_id.value)] = c
        return cursors

    async def initialize_for_project(
        self, project_id: object, engines: tuple[object, ...]
    ) -> tuple[object, ...]:
        from vibey.application.dto import RotationCursor
        from vibey.domain.engine import EngineId

        for idx, eid in enumerate(engines):
            assert isinstance(eid, EngineId)
            key = (project_id, eid.value)
            if key not in self._cursors:
                self._cursors[key] = RotationCursor(
                    project_id=project_id, engine_id=eid, current=0, order=idx
                )
        return tuple(
            c
            for (pid, _), c in sorted(self._cursors.items(), key=lambda x: x[1].order)
            if pid == project_id
        )
