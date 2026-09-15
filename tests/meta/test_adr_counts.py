# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Every advertised ADR count matches the ADRs that exist.

The count is written out in five places -- CLAUDE.md, AGENTS.md, GEMINI.md, README.md
and docs/index.md -- and by the time ADR-0020 was written four of them still said 15.
A number repeated in five hand-maintained files drifts; it had already drifted three
times. This is the cheapest thing that stops it drifting a fourth.

Deliberately not solved by deleting the count. It is useful -- it tells a reader how much
recorded reasoning is waiting for them -- and "remove the fact so it cannot be wrong" is
the wrong trade when the fact is one `glob` away from being checkable.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
DECISIONS = REPO / "docs" / "architecture" / "decisions"
ADVERTISED = ("CLAUDE.md", "AGENTS.md", "GEMINI.md", "README.md", "docs/index.md")
COUNT = re.compile(r"\((\d+) ADRs")


def _actual() -> int:
    return len(list(DECISIONS.glob("0*.md")))


@pytest.mark.parametrize("name", ADVERTISED)
def test_the_advertised_count_matches_the_adrs_on_disk(name: str) -> None:
    text = (REPO / name).read_text(encoding="utf-8")
    claimed = COUNT.findall(text)
    assert claimed, f"{name} no longer advertises an ADR count; drop it from ADVERTISED"
    actual = _actual()
    assert all(int(c) == actual for c in claimed), (
        f"{name} advertises {claimed} ADRs; {actual} exist in docs/architecture/decisions/"
    )


def test_the_numbering_has_no_gaps_or_duplicates() -> None:
    """A count is only meaningful if the range behind it is contiguous."""
    numbers = sorted(int(p.name[:4]) for p in DECISIONS.glob("0*.md"))
    assert numbers == list(range(1, len(numbers) + 1)), f"non-contiguous ADR numbering: {numbers}"


def test_every_adr_is_in_the_published_navigation() -> None:
    """An ADR absent from the nav is an ADR nobody reading the site can reach."""
    nav = (REPO / "properdocs.yml").read_text(encoding="utf-8")
    missing = [p.name for p in sorted(DECISIONS.glob("0*.md")) if p.name not in nav]
    assert not missing, f"not in properdocs.yml nav: {missing}"
