#!/usr/bin/env python3
# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Validate the vibey-skills marketplace.

Stdlib only — no dependencies, no build step. Run from anywhere:

    python3 tools/validate_manifests.py

Checks performed:

  1. `.claude-plugin/marketplace.json` and every `plugins/*/.claude-plugin/plugin.json`
     parse as JSON.
  2. Each plugin's `name` equals its directory name.
  3. Every marketplace `source` path exists and is a directory.
  4. Each marketplace entry's `version` matches that plugin's `plugin.json`.
  5. Every `plugins/*/skills/*/SKILL.md` has YAML frontmatter whose `name` equals its
     directory name and whose `description` is non-empty.
  6. Skill names are unique across the whole marketplace.
  7. `pyproject.toml`'s version equals `marketplace.json`'s `metadata.version`.

Exits 0 on success, 1 with a report of every problem found on failure. It reports *all*
failures rather than stopping at the first, so one run tells you everything to fix.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
PYPROJECT = ROOT / "pyproject.toml"

# `name: value`, tolerating quotes, in a SKILL.md frontmatter block.
FRONTMATTER_KEY = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:\s*(.*)$")


class Report:
    """Collects failures so one run surfaces every problem, not just the first."""

    def __init__(self) -> None:
        self.errors: list[str] = []

    def fail(self, message: str) -> None:
        self.errors.append(message)

    def ok(self) -> bool:
        return not self.errors


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_json(path: Path, report: Report) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        report.fail(f"{rel(path)}: file not found")
    except json.JSONDecodeError as exc:
        report.fail(f"{rel(path)}: invalid JSON — {exc}")
    return None


def parse_frontmatter(path: Path, report: Report) -> dict[str, str] | None:
    """Parse the leading `---` fenced block of a SKILL.md.

    Deliberately not a general YAML parser: skill frontmatter is a flat map of scalars,
    and depending on PyYAML would make this validator non-stdlib. Values may be wrapped
    in matching quotes and may span continuation lines (a folded description).
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        report.fail(f"{rel(path)}: unreadable — {exc}")
        return None

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        report.fail(f"{rel(path)}: missing YAML frontmatter (file must start with '---')")
        return None

    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        report.fail(f"{rel(path)}: frontmatter block is never closed with '---'")
        return None

    fields: dict[str, str] = {}
    key: str | None = None
    for raw in lines[1:end]:
        match = FRONTMATTER_KEY.match(raw)
        if match and not raw.startswith((" ", "\t")):
            key, value = match.group(1), match.group(2).strip()
            fields[key] = value
        elif key is not None and raw.strip():
            # Continuation of a wrapped value.
            fields[key] = f"{fields[key]} {raw.strip()}".strip()

    for name, value in list(fields.items()):
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            fields[name] = value[1:-1]
    return fields


def pyproject_version(report: Report) -> str | None:
    """Read `version` from pyproject, or resolve it from the package when it is dynamic."""
    try:
        text = PYPROJECT.read_text(encoding="utf-8")
    except FileNotFoundError:
        report.fail("pyproject.toml: file not found")
        return None

    static = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if static:
        return static.group(1)

    if re.search(r"^dynamic\s*=\s*\[[^\]]*\bversion\b", text, re.MULTILINE):
        init = ROOT / "src" / "vibey_skills" / "__init__.py"
        try:
            source = init.read_text(encoding="utf-8")
        except FileNotFoundError:
            report.fail(f"{rel(init)}: not found, but pyproject declares a dynamic version")
            return None
        match = re.search(r'^__version__\s*=\s*"([^"]+)"', source, re.MULTILINE)
        if not match:
            report.fail(f"{rel(init)}: no __version__ assignment found")
            return None
        return match.group(1)

    report.fail("pyproject.toml: no static or dynamic project version found")
    return None


def main() -> int:
    report = Report()

    market = load_json(MARKETPLACE, report)
    if market is None:
        print("FAILED:", file=sys.stderr)
        for error in report.errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    entries = market.get("plugins", [])
    entry_by_name = {e.get("name"): e for e in entries}
    if len(entry_by_name) != len(entries):
        report.fail("marketplace.json: duplicate plugin names in `plugins`")

    # The context engine owns the optional retrieval metadata schema. Importing it from
    # source keeps this validator dependency-free while ensuring malformed list values,
    # unsupported schema versions, symlink escapes, duplicates, and nonexistent mandatory
    # headings fail in the same command contributors and CI already run.
    try:
        sys.path.insert(0, str(ROOT / "src"))
        from vibey_skills.context_engine import ContextEngineError, build_manifest

        build_manifest(ROOT / "plugins")
    except (ContextEngineError, OSError, ValueError) as exc:
        report.fail(f"retrieval metadata/corpus validation failed: {exc}")

    # --- marketplace entries ---------------------------------------------
    for entry in entries:
        name = entry.get("name")
        source = entry.get("source")
        if not name or not source:
            report.fail(f"marketplace.json: entry missing name/source — {entry!r}")
            continue

        source_dir = (ROOT / source).resolve()
        if not source_dir.is_dir():
            report.fail(f"marketplace.json[{name}]: source does not exist — {source}")
            continue
        if source_dir.name != name:
            report.fail(
                f"marketplace.json[{name}]: source directory is '{source_dir.name}', "
                f"expected '{name}'"
            )

        manifest_path = source_dir / ".claude-plugin" / "plugin.json"
        manifest = load_json(manifest_path, report)
        if manifest is None:
            continue
        if manifest.get("name") != name:
            report.fail(
                f"{rel(manifest_path)}: name is {manifest.get('name')!r}, "
                f"expected {name!r} (must match directory and marketplace entry)"
            )
        if manifest.get("version") != entry.get("version"):
            report.fail(
                f"{name}: version mismatch — marketplace says {entry.get('version')!r}, "
                f"plugin.json says {manifest.get('version')!r}"
            )

    # --- every plugin.json on disk is registered --------------------------
    plugin_dirs = sorted(p for p in (ROOT / "plugins").iterdir() if p.is_dir())
    for plugin_dir in plugin_dirs:
        manifest_path = plugin_dir / ".claude-plugin" / "plugin.json"
        if not manifest_path.is_file():
            report.fail(f"{rel(plugin_dir)}: missing .claude-plugin/plugin.json")
            continue
        manifest = load_json(manifest_path, report)
        if manifest is None:
            continue
        if manifest.get("name") != plugin_dir.name:
            report.fail(
                f"{rel(manifest_path)}: name is {manifest.get('name')!r}, "
                f"expected directory name {plugin_dir.name!r}"
            )
        if plugin_dir.name not in entry_by_name:
            report.fail(
                f"{rel(plugin_dir)}: plugin exists on disk but has no marketplace.json entry"
            )

    # --- skills ------------------------------------------------------------
    seen_skills: dict[str, str] = {}
    skill_count = 0
    for skill_md in sorted((ROOT / "plugins").glob("*/skills/*/SKILL.md")):
        skill_count += 1
        skill_dir = skill_md.parent
        fields = parse_frontmatter(skill_md, report)
        if fields is None:
            continue

        name = fields.get("name", "")
        if not name:
            report.fail(f"{rel(skill_md)}: frontmatter has no `name`")
        elif name != skill_dir.name:
            report.fail(
                f"{rel(skill_md)}: frontmatter name is {name!r}, "
                f"expected directory name {skill_dir.name!r}"
            )

        if not fields.get("description", "").strip():
            report.fail(f"{rel(skill_md)}: frontmatter `description` is missing or empty")

        if name:
            if name in seen_skills:
                report.fail(
                    f"duplicate skill name {name!r}: {seen_skills[name]} and {rel(skill_md)}"
                )
            else:
                seen_skills[name] = rel(skill_md)

    # --- version single-sourcing -------------------------------------------
    manifest_version = (market.get("metadata") or {}).get("version")
    package_version = pyproject_version(report)
    if package_version is not None and manifest_version != package_version:
        report.fail(
            f"version mismatch — marketplace.json metadata.version is {manifest_version!r}, "
            f"pyproject/package version is {package_version!r}"
        )

    # --- report -------------------------------------------------------------
    if not report.ok():
        print(f"FAILED — {len(report.errors)} problem(s):", file=sys.stderr)
        for error in report.errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print(
        f"ok — {len(entries)} plugins, {skill_count} skills, "
        f"version {manifest_version}; all manifests, sources, and frontmatter valid"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
