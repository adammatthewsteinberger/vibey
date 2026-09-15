#!/usr/bin/env python3
# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Pick which plugins the weekly currency audit should research, and brief the agent.

Stdlib only, like the other checkers. Run from anywhere:

    python3 tools/select_currency_batch.py                 # this week's slice, as markdown
    python3 tools/select_currency_batch.py --format names  # one plugin name per line
    python3 tools/select_currency_batch.py --plugins a,b   # explicit override

Why a rotation rather than "audit everything"
---------------------------------------------
The marketplace is far too large to re-research in one run, and most of it does not go
stale: the second law, Clausewitz and wood movement will read the same next year. So the
job walks a deterministic slice each week, keyed on the ISO week number, and every plugin
comes round on a fixed cycle. Deterministic matters more than clever here — the same week
always selects the same plugins, so a run can be reproduced locally, and no state file has
to be carried between runs.

Ordering is by the marketplace's own plugin order (alphabetical), so adding a plugin
shifts the cycle slightly rather than reshuffling it.

The briefing
------------
Generated skills carry a `> **Currency:**` line naming the section that holds their dated
claims, e.g. "See §26 → `hw-reference` for grid power as the binding constraint". That line
is exactly the research brief for the plugin, so it is extracted and printed rather than
making the agent hunt for it. A plugin with no such line is still listed — hand-written
skills can go stale too — but it is marked so the agent knows there is no dated anchor to
check against.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"

# The header blockquote a generated skill carries, e.g.
#   > **Currency:** The physics is settled. Two areas moved. See §26 → `hw-reference` for …
CURRENCY = re.compile(r"^> \*\*Currency:\*\*\s*(.+?)\s*$", re.M)


def plugin_names() -> list[str]:
    data = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
    return [p["name"] for p in data["plugins"]]


def currency_note(plugin: str) -> str | None:
    """The first `> **Currency:**` line found among a plugin's skills, if any."""
    for skill in sorted((ROOT / "plugins" / plugin / "skills").glob("*/SKILL.md")):
        match = CURRENCY.search(skill.read_text(encoding="utf-8"))
        if match:
            return match.group(1)
    return None


def select(names: list[str], per_run: int, week: int) -> list[str]:
    """A contiguous, wrapping slice of `names`, advancing by `per_run` each week."""
    if not names:
        return []
    per_run = max(1, min(per_run, len(names)))
    start = (week * per_run) % len(names)
    return [names[(start + i) % len(names)] for i in range(per_run)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--per-run", type=int, default=4, help="how many plugins to audit in one run (default: 8)"
    )
    parser.add_argument(
        "--week", type=int, default=None, help="ISO week number to select for (default: this week)"
    )
    parser.add_argument(
        "--plugins", default=None, help="comma-separated plugin names, bypassing the rotation"
    )
    parser.add_argument("--format", choices=("markdown", "names", "json"), default="markdown")
    args = parser.parse_args()

    names = plugin_names()
    if args.plugins:
        chosen = [p.strip() for p in args.plugins.split(",") if p.strip()]
        unknown = [p for p in chosen if p not in names]
        if unknown:
            print(f"unknown plugin(s): {', '.join(unknown)}", file=sys.stderr)
            return 1
    else:
        week = args.week if args.week is not None else dt.date.today().isocalendar()[1]
        chosen = select(names, args.per_run, week)

    if args.format == "names":
        print("\n".join(chosen))
        return 0
    if args.format == "json":
        print(json.dumps([{"name": p, "currency": currency_note(p)} for p in chosen], indent=2))
        return 0

    cycle = (len(names) + args.per_run - 1) // args.per_run
    print(
        f"## Plugins to audit this run ({len(chosen)} of {len(names)}; full cycle ≈ {cycle} runs)\n"
    )
    for p in chosen:
        note = currency_note(p)
        print(f"### {p}\n")
        print(f"- Skills: `plugins/{p}/skills/*/SKILL.md`")
        if note:
            print(f"- Currency note: {note}")
        else:
            print(
                "- Currency note: none — this plugin has no dated anchor. Only propose a "
                "change if you find something that plainly contradicts the text."
            )
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
