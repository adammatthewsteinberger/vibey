# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Report which releases on an index have been superseded by the one just published.

**This reports. It cannot yank, because PyPI provides no way to.** An earlier version of
this module POSTed `:action=yank` to the legacy upload endpoint. That action does not
exist: the endpoint answers `405 Method Not Allowed`, while a recognised action such as
`:action=file_upload` answers `403` on bad credentials. Auth is never reached, so no token
makes it work.

Yanking is a browser-only operation. PyPI's own documentation gives exactly one method --
the release management page, Options, Yank
(https://docs.pypi.org/project-management/yanking/) -- and the `/manage/...` route it uses
is CSRF-protected against non-browser callers. Programmatic access is an open request
upstream, not a shipped capability:

- https://github.com/pypa/packaging-problems/issues/633
- https://github.com/pypi/warehouse/issues/12708

That is arguably the correct design. PEP 592 defines a yanked release as one with "a
serious problem which should prevent it from being installed" -- a distress signal, not a
tidiness marker. Installers still resolve a yanked version when a pin demands it, so
nothing is reclaimed; what changes is that everyone pinned to it starts seeing a warning
about a release that may be perfectly good. The manual click is the friction that keeps
that deliberate.

So the analysis is automated and the click is left to a human: this works out exactly which
releases are superseded, honouring `keep`, and prints them with a direct link to the page
where they can be actioned.
"""

from __future__ import annotations

import fnmatch
import json
import urllib.error
import urllib.request
from dataclasses import dataclass

from vibey_gh.config import GhConfig

PYPI = "pypi"
TESTPYPI = "testpypi"

_INDEX_JSON = {
    PYPI: "https://pypi.org/pypi/{project}/json",
    TESTPYPI: "https://test.pypi.org/pypi/{project}/json",
}
# Where a human actually performs the yank. Printed beside the list so acting on it is one
# click rather than a hunt through the project settings.
_MANAGE = {
    PYPI: "https://pypi.org/manage/project/{project}/releases/",
    TESTPYPI: "https://test.pypi.org/manage/project/{project}/releases/",
}


@dataclass
class SupersededReport:
    index: str
    superseded: tuple[str, ...] = ()
    skipped: tuple[str, ...] = ()
    problems: tuple[str, ...] = ()
    manage_url: str = ""
    # Article V.4: this release ratified a governance change, so everything below it is
    # named without a retention window and regardless of the per-index switches.
    governance: bool = False

    @property
    def ok(self) -> bool:
        return not self.problems


def governance_changed(patterns: tuple[str, ...], changed: list[str]) -> bool:
    """Did this release ratify a governance change? fnmatch globs over changed paths.

    Pure on purpose: the caller supplies the changed-file list (git is its problem), so
    the rule itself is testable byte-for-byte and never depends on repository state.
    """
    return any(fnmatch.fnmatch(path, pattern) for path in changed for pattern in patterns)


def released_versions(index: str, project: str, timeout: int = 30) -> list[str]:
    """Every version the index holds that is not already yanked.

    A release whose files are all yanked is already in the state a yank would put it in, so
    it is not reported -- listing it again would be noise in a report whose whole purpose is
    to be a short, actionable list.
    """
    url = _INDEX_JSON[index].format(project=project)
    try:
        # `url` is _INDEX_JSON[index], a literal https:// template chosen by a two-value
        # key. There is no scheme here a caller could influence.
        with urllib.request.urlopen(url, timeout=timeout) as response:  # nosec B310
            payload = json.loads(response.read())
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return []
        raise
    versions: list[str] = []
    for version, files in (payload.get("releases") or {}).items():
        if not files:
            continue
        if all(item.get("yanked") for item in files):
            continue
        versions.append(version)
    return versions


def order(version: str) -> tuple[int, ...] | None:
    """A sortable key for `N.N.N` and `N.N.N.devN`, or None if this cannot parse it.

    Deliberately not a PEP 440 implementation. This project has no dependencies, so
    `packaging` is not available, and half a version parser applied to epochs, local
    segments and post-releases would mis-order them silently -- which here means naming a
    good release in a list of things to yank. Anything outside the shape this project
    publishes returns None and is left out.

    A release sorts ABOVE its own dev builds: `1.2.0.dev5` precedes `1.2.0`, which is what
    makes a final release supersede the dev builds that anticipated it.
    """
    base, separator, dev = version.partition(".dev")
    parts = base.split(".")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        return None
    # `separator`, not `dev`: `1.2.0.dev` has the marker and an empty number, and testing
    # the number alone let it fall through and parse as the FINAL release `1.2.0` -- a
    # malformed version silently read as a real one.
    if separator and not dev.isdigit():
        return None
    major, minor, patch = (int(part) for part in parts)
    # A final release is (…, 1, 0); a dev build of it is (…, 0, N) and so sorts first.
    return (major, minor, patch, 0, int(dev)) if dev else (major, minor, patch, 1, 0)


def supersede(versions: list[str], current: str, keep: int) -> list[str]:
    """Which versions are superseded: everything below `current`, minus the newest `keep`.

    `current` is excluded by identity, not by ordering -- naming the release that was just
    published as a candidate for yanking would be worse than useless, and leaving that to a
    version comparison is one parsing quirk away from exactly that.
    """
    here = order(current)
    if here is None:
        return []
    candidates = []
    for version in versions:
        if version == current:
            continue
        other = order(version)
        if other is None:
            continue
        if other < here:
            candidates.append((other, version))
    candidates.sort(reverse=True)
    return [version for _, version in candidates[keep:]]


def report_superseded(
    cfg: GhConfig,
    index: str,
    project: str,
    current: str,
    changed_files: list[str] | None = None,
) -> SupersededReport:
    """Work out what `current` supersedes on `index`, honouring `keep`.

    When `changed_files` shows a ratified governance change (Article V.4 of the
    Constitution), the retention window and the per-index off-switches are overridden:
    every previous release is named, zero exceptions. The rule outranks the config
    because the config is machinery and the rule is law.
    """
    governance = governance_changed(cfg.yank.governance_paths, changed_files or [])
    enabled = cfg.yank.pypi if index == PYPI else cfg.yank.testpypi
    if not enabled and not governance:
        return SupersededReport(index, skipped=("disabled",))

    try:
        versions = released_versions(index, project)
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as error:
        # Never fail the release over this. The package is already published; a failure here
        # is bookkeeping, and turning it into a red release would misreport a successful
        # publish as a broken one.
        return SupersededReport(index, problems=(f"could not read {index}: {error}",))

    targets = supersede(versions, current, 0 if governance else cfg.yank.keep)
    if not targets:
        return SupersededReport(index, skipped=("nothing superseded",), governance=governance)
    return SupersededReport(
        index,
        superseded=tuple(targets),
        manage_url=_MANAGE[index].format(project=project),
        governance=governance,
    )
