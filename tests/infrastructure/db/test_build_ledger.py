# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

from vibey.application.dto import EngineEvent
from vibey.domain.engine import EngineId
from vibey.infrastructure.db.build_ledger import PostgresBuildLedger


async def test_record_appends_draft_for_recognized_event_kind() -> None:
    mock_ledger = AsyncMock()
    build_ledger = PostgresBuildLedger(mock_ledger)

    event = EngineEvent(kind="SessionSeeded", at=datetime.now(UTC), payload={})
    await build_ledger.record(
        project_id=uuid4(),
        cycle=1,
        job_id=uuid4(),
        engine_id=EngineId.CLAUDELOOP,
        correlation_id=uuid4(),
        event=event,
    )

    mock_ledger.append.assert_called_once()


async def test_record_skips_append_for_unrecognized_event_kind() -> None:
    mock_ledger = AsyncMock()
    build_ledger = PostgresBuildLedger(mock_ledger)

    event = EngineEvent(kind="CompletelyFakeKind", at=datetime.now(UTC), payload={})
    await build_ledger.record(
        project_id=uuid4(),
        cycle=1,
        job_id=uuid4(),
        engine_id=EngineId.CLAUDELOOP,
        correlation_id=uuid4(),
        event=event,
    )

    mock_ledger.append.assert_not_called()
