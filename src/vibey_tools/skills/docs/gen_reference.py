# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Generate the skills reference from `plugins/**` at docs-build time.

`plugins/` is the marketplace's single source of truth: Claude Code reads
`.claude-plugin/marketplace.json` at the repo root with `source: ./plugins/<name>`, and the
wheel maps that same tree in via hatchling `force-include`. Copying 644 `SKILL.md` files into
`docs/` would create a second copy to drift, so this script synthesises the pages instead —
nothing it writes ever touches the working tree (mkdocs-gen-files writes into the build).

Emits, under `reference/`:
    index.md                      the plugin table
    <plugin>/index.md             that plugin's README
    <plugin>/<skill>.md           that skill's SKILL.md body
    .nav.md                       nav, consumed by mkdocs-literate-nav
                                  (dot-prefixed so mkdocs does not also render it as a page)

Link rewriting is the fiddly part and the reason this is a script rather than a glob. A
`SKILL.md` living at `plugins/<p>/skills/<s>/SKILL.md` may point at repo paths that do not
exist at the generated page's URL, so any relative target is rewritten to an absolute
GitHub URL. Absolute links are also what README.md uses, for the same underlying reason:
the docs render at three different base URLs and only absolute links survive all three.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import mkdocs_gen_files

SLUG = "adammatthewsteinberger/vibey-skills"
BLOB = f"https://github.com/{SLUG}/blob/main"

ROOT = Path(__file__).resolve().parent.parent
PLUGINS = ROOT / "plugins"
MANIFEST = ROOT / ".claude-plugin" / "marketplace.json"

FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)
RELATIVE_LINK = re.compile(r"\]\((?!https?://|#|mailto:)([^)]+)\)")


def split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Return (frontmatter fields we care about, body). Deliberately not a YAML parser:
    SKILL.md frontmatter is a flat two-key mapping, and adding a PyYAML dependency to the
    docs build to read `name:` and `description:` would not earn its keep."""
    m = FRONTMATTER.match(text)
    if not m:
        return {}, text
    fields: dict[str, str] = {}
    key = None
    for raw in m.group(1).splitlines():
        if not raw.strip():
            continue
        if re.match(r"^[A-Za-z_][A-Za-z0-9_-]*:", raw):
            key, _, value = raw.partition(":")
            key = key.strip()
            fields[key] = value.strip().strip("'\"")
        elif key:  # folded continuation line
            fields[key] = f"{fields[key]} {raw.strip()}".strip()
    return fields, text[m.end() :]


def absolutise(text: str, source_dir: str) -> str:
    """Rewrite relative Markdown links against the repo, as absolute GitHub URLs."""

    def sub(m: re.Match[str]) -> str:
        target = m.group(1)
        path, _, frag = target.partition("#")
        frag = f"#{frag}" if frag else ""
        if not path:  # pure anchor within the page — already valid
            return m.group(0)
        resolved = (ROOT / source_dir / path).resolve()
        try:
            rel = resolved.relative_to(ROOT)
        except ValueError:
            return m.group(0)  # escapes the repo; leave it for check_links.py to flag
        return f"]({BLOB}/{rel}{frag})"

    return RELATIVE_LINK.sub(sub, text)


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entries = {e["name"]: e for e in manifest["plugins"]}

    summary: list[str] = ["* [Overview](index.md)"]
    rows: list[str] = [
        "| Plugin | Version | Category | Skills |",
        "|---|---|---|---|",
    ]
    total_skills = 0

    for name in sorted(entries):
        entry = entries[name]
        plugin_dir = PLUGINS / name
        skills_dir = plugin_dir / "skills"
        skills = sorted(p.name for p in skills_dir.iterdir() if (p / "SKILL.md").is_file())
        total_skills += len(skills)

        rows.append(
            f"| [{name}]({name}/index.md) | `{entry.get('version', '')}` "
            f"| {entry.get('category', '')} | {len(skills)} |"
        )

        # ---- plugin landing page, from its README ----
        readme = plugin_dir / "README.md"
        body = readme.read_text(encoding="utf-8") if readme.is_file() else f"# {name}\n"
        body = absolutise(body, f"plugins/{name}")
        with mkdocs_gen_files.open(f"reference/{name}/index.md", "w") as fd:
            fd.write(body)
            fd.write("\n\n## Skills in this plugin\n\n")
            for skill in skills:
                fd.write(f"- [{skill}]({skill}.md)\n")
            fd.write(f"\n---\n\n[View `{name}` on GitHub]({BLOB}/plugins/{name})\n")
        mkdocs_gen_files.set_edit_path(f"reference/{name}/index.md", f"../plugins/{name}/README.md")

        summary.append(f"* [{name}](" + f"{name}/index.md)")
        sub_items: list[str] = []

        # ---- one page per skill ----
        for skill in skills:
            src = skills_dir / skill / "SKILL.md"
            fields, skill_body = split_frontmatter(src.read_text(encoding="utf-8"))
            skill_body = absolutise(skill_body, f"plugins/{name}/skills/{skill}")

            with mkdocs_gen_files.open(f"reference/{name}/{skill}.md", "w") as fd:
                # Re-emit the trigger description as page meta so search indexes it and
                # Material renders it as the meta description.
                if fields.get("description"):
                    desc = fields["description"].replace("\n", " ")
                    fd.write("---\n")
                    fd.write(f"description: {json.dumps(desc)}\n")
                    fd.write("---\n\n")
                if not skill_body.lstrip().startswith("#"):
                    fd.write(f"# {skill}\n\n")
                fd.write(skill_body.lstrip("\n"))
                fd.write(
                    f"\n\n---\n\n**Plugin:** [{name}](index.md) · "
                    f"[View `SKILL.md` on GitHub]"
                    f"({BLOB}/plugins/{name}/skills/{skill}/SKILL.md)\n"
                )
            mkdocs_gen_files.set_edit_path(
                f"reference/{name}/{skill}.md",
                f"../plugins/{name}/skills/{skill}/SKILL.md",
            )
            sub_items.append(f"    * [{skill}]({name}/{skill}.md)")

        summary.extend(sub_items)

    # ---- reference overview ----
    with mkdocs_gen_files.open("reference/index.md", "w") as fd:
        fd.write("# Skills reference\n\n")
        fd.write(
            f"**{len(entries)} plugins** and **{total_skills} skills**. Every page here is "
            "generated from the marketplace tree at build time, so it cannot drift from what "
            "the plugins actually ship.\n\n"
        )
        fd.write("\n".join(rows))
        fd.write("\n")

    with mkdocs_gen_files.open("reference/.nav.md", "w") as fd:
        fd.write("\n".join(summary) + "\n")


main()
