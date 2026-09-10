#!/usr/bin/env python3
"""CI check: validate every .claude/skills/*/SKILL.md's YAML frontmatter.

Claude Code itself performs NO validation of SKILL.md frontmatter — malformed
YAML loads silently with empty metadata, and the skill simply never triggers
(see docs/architecture/decisions/ for the broader "no silent gaps" theme this
project applies everywhere else too). This script is the enforcement Claude
Code doesn't provide: it fails loudly, in CI, on exactly the mistakes that
would otherwise fail silently at runtime.

Checks per SKILL.md:
  - The file starts with valid `---`-delimited YAML frontmatter.
  - `name` is present and matches the parent directory name exactly (the
    Agent Skills spec's portability rule; Claude Code doesn't enforce this
    itself, but keeping it true means these skills stay valid if ever
    packaged for claude.ai / the Skills API).
  - `description` is present and non-empty.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

SKILLS_DIR = Path(__file__).resolve().parent.parent / ".claude" / "skills"


def extract_frontmatter(text: str) -> str | None:
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    return parts[1]


def check_skill(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return [f"{skill_dir}: missing SKILL.md"]

    text = skill_md.read_text(encoding="utf-8")
    raw_frontmatter = extract_frontmatter(text)
    if raw_frontmatter is None:
        return [f"{skill_md}: no valid '---'-delimited frontmatter block found"]

    try:
        data = yaml.safe_load(raw_frontmatter)
    except yaml.YAMLError as exc:
        return [f"{skill_md}: frontmatter is not valid YAML ({exc})"]

    if not isinstance(data, dict):
        return [f"{skill_md}: frontmatter did not parse to a mapping"]

    name = data.get("name")
    if not name:
        errors.append(f"{skill_md}: missing required 'name' field")
    elif name != skill_dir.name:
        errors.append(
            f"{skill_md}: 'name: {name}' does not match directory name '{skill_dir.name}'"
        )

    description = data.get("description")
    if not description or not str(description).strip():
        errors.append(f"{skill_md}: missing or empty required 'description' field")

    return errors


def main() -> int:
    if not SKILLS_DIR.is_dir():
        print(f"No skills directory at {SKILLS_DIR} — nothing to check.")
        return 0

    all_errors: list[str] = []
    skill_dirs = sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir())
    if not skill_dirs:
        print(f"No skill directories found under {SKILLS_DIR}.")
        return 0

    for skill_dir in skill_dirs:
        all_errors.extend(check_skill(skill_dir))

    if all_errors:
        print(f"Found {len(all_errors)} skill frontmatter problem(s):\n", file=sys.stderr)
        for error in all_errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print(f"All {len(skill_dirs)} skills have valid frontmatter.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
