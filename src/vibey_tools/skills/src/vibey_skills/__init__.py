# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""vibey-skills — Agent Skills packaged as a Claude Code plugin marketplace.

Formerly ``vibe-engineering-skills`` (import name ``vibe_engineering_skills``); renamed in 2.0.0.

The ``plugins/`` tree lives at the repository root because Claude Code requires
``.claude-plugin/marketplace.json`` there with ``source: ./plugins/<name>``. The wheel
*force-includes* that same tree under this package rather than duplicating it, so there is
exactly one copy of every skill file.

That means the data lives in two different places depending on how the code is running:

* installed from a wheel  -> ``<site-packages>/vibey_skills/plugins``
* run from a source checkout -> ``<repo-root>/plugins``

:func:`plugins_root` and :func:`marketplace_manifest` resolve both, so the CLI works either
way without the caller caring.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

__version__ = "2.19.10"

__all__ = [
    "__version__",
    "Skill",
    "iter_skills",
    "marketplace_manifest",
    "marketplace_manifest_path",
    "plugins_root",
]

_PACKAGE_DIR = Path(__file__).resolve().parent
# From src/vibey_skills/__init__.py, the repo root is three levels up.
_REPO_ROOT = _PACKAGE_DIR.parent.parent


@dataclass(frozen=True)
class Skill:
    """One ``SKILL.md`` and the metadata Claude uses to decide whether to load it."""

    plugin: str
    name: str
    description: str
    path: Path

    @property
    def directory(self) -> Path:
        """The skill directory — what gets copied into ``~/.claude/skills``."""
        return self.path.parent


def plugins_root() -> Path:
    """Return the directory holding the plugin tree.

    Prefers the packaged copy (``importlib.resources`` semantics via ``__file__``, which is
    correct for a normal wheel install), and falls back to the repository root so the CLI
    behaves identically from a source checkout.
    """
    packaged = _PACKAGE_DIR / "plugins"
    if packaged.is_dir():
        return packaged

    source = _REPO_ROOT / "plugins"
    if source.is_dir():
        return source

    raise FileNotFoundError(
        "vibey-skills: could not locate the plugins directory in either "
        f"{packaged} or {source}. The installation looks incomplete."
    )


def marketplace_manifest_path() -> Path:
    """Return the path to ``marketplace.json`` for ``/plugin marketplace add``."""
    packaged = _PACKAGE_DIR / "marketplace.json"
    if packaged.is_file():
        return packaged

    source = _REPO_ROOT / ".claude-plugin" / "marketplace.json"
    if source.is_file():
        return source

    raise FileNotFoundError(
        "vibey-skills: could not locate marketplace.json in either "
        f"{packaged} or {source}. The installation looks incomplete."
    )


def marketplace_manifest() -> dict:
    """Return the parsed marketplace manifest."""
    return json.loads(marketplace_manifest_path().read_text(encoding="utf-8"))


def _parse_frontmatter(text: str) -> dict[str, str]:
    """Extract the leading ``---`` fenced block of a SKILL.md as a flat mapping.

    Skill frontmatter is a flat map of scalar values, so a tiny purpose-built reader keeps
    this package dependency-free rather than pulling in PyYAML for four lines of metadata.
    Wrapped values (a description spilling onto the next line) are folded back together.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return {}

    fields: dict[str, str] = {}
    key: str | None = None
    for raw in lines[1:end]:
        stripped = raw.strip()
        if not stripped:
            continue
        if not raw[:1].isspace() and ":" in stripped:
            candidate, _, value = stripped.partition(":")
            if candidate and all(c.isalnum() or c in "_-" for c in candidate):
                key = candidate
                fields[key] = value.strip()
                continue
        if key is not None:
            fields[key] = f"{fields[key]} {stripped}".strip()

    for name, value in list(fields.items()):
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            fields[name] = value[1:-1]
    return fields


def iter_skills(plugin: str | None = None):
    """Yield every :class:`Skill`, sorted by plugin then skill name.

    Args:
        plugin: restrict the results to a single plugin name.
    """
    root = plugins_root()
    plugin_dirs = sorted(p for p in root.iterdir() if p.is_dir())
    if plugin is not None:
        plugin_dirs = [p for p in plugin_dirs if p.name == plugin]

    for plugin_dir in plugin_dirs:
        skills_dir = plugin_dir / "skills"
        if not skills_dir.is_dir():
            continue
        for skill_dir in sorted(p for p in skills_dir.iterdir() if p.is_dir()):
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.is_file():
                continue
            fields = _parse_frontmatter(skill_md.read_text(encoding="utf-8"))
            yield Skill(
                plugin=plugin_dir.name,
                name=fields.get("name") or skill_dir.name,
                description=fields.get("description", ""),
                path=skill_md,
            )
