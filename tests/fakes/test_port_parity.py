# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Port parity: every Fake satisfies its Protocol at the structural level.

Modelled after codexloop/tests/application/test_ports.py — a parametrized
table of (name, fake_instance, Protocol) triples so a new fake that forgets
a method fails immediately instead of only when a specific test happens to
call it.
"""

import pytest

from tests.fakes import (
    FakeEngineHealthRepository,
    FakeHumanGateRepository,
    FakeJobRepository,
    FakeRotationCursorRepository,
)
from vibey.application.interfaces.engines import (
    EngineHealthRepository,
    RotationCursorRepository,
)
from vibey.application.interfaces.gates import HumanGateRepository
from vibey.application.interfaces.queue import JobRepository

_PORT_TABLE: list[tuple[str, object, type]] = [
    ("JobRepository", FakeJobRepository(), JobRepository),
    ("HumanGateRepository", FakeHumanGateRepository(), HumanGateRepository),
    ("EngineHealthRepository", FakeEngineHealthRepository(), EngineHealthRepository),
    ("RotationCursorRepository", FakeRotationCursorRepository(), RotationCursorRepository),
]


@pytest.mark.parametrize(
    ("name", "fake", "protocol"),
    _PORT_TABLE,
    ids=[t[0] for t in _PORT_TABLE],
)
def test_fake_satisfies_protocol(name: str, fake: object, protocol: type) -> None:
    assert isinstance(fake, protocol), (
        f"Fake{name} does not satisfy {protocol.__name__} — missing or mismatched methods"
    )
