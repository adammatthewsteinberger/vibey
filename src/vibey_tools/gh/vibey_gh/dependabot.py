# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Keeping a well-meaning bot out of files it does not know are managed (#273).

Managed workflows have exactly one source of truth: the template they were rendered
from. Their action pins are maintained upstream and arrive through the version wave.
Dependabot does not know that. It bumps `uses:` pins wherever it finds them, the
rendered bytes stop matching the template, `installed()` reports the file out of
date, and the pre-push hook then refuses **every** push from that branch — including
the promotion to main. A routine dependency bump silently wedges the release path.

That is not hypothetical: it happened on qwenloop (its PR #20), and the diagnosis
went through three wrong hypotheses before a merge timestamp gave it away. Nothing
in a managed workflow marks it as managed — it carries the same provenance header a
hand-authored one does — so neither the bot nor the human reading the diff has a way
to tell.

**Dependabot cannot be told to skip a file.** Its `github-actions` ecosystem scans
every workflow under the repository, and `ignore:` matches on *dependency name*, not
path. So the protection is necessarily an ignore list of the actions the templates
themselves pin, derived here from the templates rather than hand-maintained — the
list moves when the templates move.

This module never rewrites an existing `dependabot.yml`. Editing someone's
configuration with string surgery, in a package that deliberately carries no YAML
dependency, is a good way to turn a lint into an outage. Absent, it is written;
present but unprotected, it is *reported*, with the exact lines to add.
"""

from __future__ import annotations

import re
from pathlib import Path

__all__ = [
    "DEPENDABOT_PATH",
    "desired_config",
    "differs_only_in_action_pins",
    "template_actions",
    "unprotected_actions",
]

DEPENDABOT_PATH = ".github/dependabot.yml"

# `uses: owner/repo@ref` and `uses: owner/repo/path@ref`. Local (`./`) and docker
# (`docker://`) uses are not dependabot github-actions dependencies.
_USES = re.compile(r"^\s*(?:-\s*)?uses:\s*['\"]?([A-Za-z0-9][\w.-]*/[\w.-]+)(?:/[^@'\"\s]*)?@")


def template_actions(sources: list[Path]) -> tuple[str, ...]:
    """Every `owner/repo` action the given managed templates pin, sorted and unique."""
    found: set[str] = set()
    for source in sources:
        try:
            text = source.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines():
            match = _USES.match(line)
            if match:
                found.add(match.group(1))
    return tuple(sorted(found))


def desired_config(actions: tuple[str, ...]) -> str:
    """A fresh `dependabot.yml` that keeps the bot away from the managed pins.

    Deliberately minimal. It configures the one ecosystem this module has an opinion
    about and leaves every other ecosystem to the adopter, because a file written by
    tooling should not quietly become the place someone's pip policy lives.
    """
    ignores = "\n".join(f"      - dependency-name: {name}" for name in actions)
    return (
        "version: 2\n"
        "updates:\n"
        "  - package-ecosystem: github-actions\n"
        "    directory: /\n"
        "    schedule:\n"
        "      interval: weekly\n"
        "    # vibey-gh owns the action versions used by the workflows it generates, and\n"
        "    # ships them through its own releases. A bump applied here instead makes the\n"
        "    # rendered file stop matching its template, which fails `vibey-gh check` and\n"
        "    # makes the pre-push hook refuse every push from the branch — including the\n"
        "    # promotion to main. Upgrade these by upgrading vibey-gh.\n"
        "    #\n"
        "    # Dependabot cannot ignore a FILE, only a dependency, so these names are the\n"
        "    # actions the managed templates pin. Actions absent from this list are still\n"
        "    # bumped normally wherever you use them.\n"
        "    ignore:\n" + ignores + "\n"
    )


def unprotected_actions(root: Path, actions: tuple[str, ...]) -> tuple[str, ...]:
    """Which managed pins a present `dependabot.yml` leaves exposed.

    Empty when the file is absent (nothing is scanning, so nothing is exposed) or when
    it configures no `github-actions` ecosystem at all. Matching is textual on purpose:
    the question is only "does this configuration name this dependency", and answering
    it does not justify taking a YAML dependency into a stdlib-only package.
    """
    config = root / DEPENDABOT_PATH
    try:
        text = config.read_text(encoding="utf-8")
    except OSError:
        return ()
    if "github-actions" not in text:
        return ()
    # `(?![\w./-])` rather than `\b`: a word boundary sits between "checkout" and the
    # hyphen of "actions/checkout-extra", so `\b` would read an unrelated entry as
    # protection for `actions/checkout` — silently reporting a repository safe when the
    # very pin at issue is still exposed.
    return tuple(
        name
        for name in actions
        if not re.search(rf"dependency-name:\s*['\"]?{re.escape(name)}(?![\w./-])", text)
    )


def differs_only_in_action_pins(installed: str, rendered: str) -> bool:
    """Whether two versions of a managed workflow differ *only* in `uses:` pins.

    This is the signature of a bot edit, and naming it is the difference between a
    one-line diagnosis and an evening of them. It is a heuristic and is only ever used
    to add an explanation to a message that is already correct without it.
    """
    left, right = installed.splitlines(), rendered.splitlines()
    if len(left) != len(right):
        return False
    differing = [(a, b) for a, b in zip(left, right) if a != b]
    if not differing:
        return False
    return all(_USES.match(a) and _USES.match(b) for a, b in differing)
