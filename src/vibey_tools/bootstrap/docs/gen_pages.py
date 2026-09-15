"""Generate the MkDocs site from the repo-root markdown sources.

Executed by mkdocs-gen-files during `mkdocs build` / `mkdocs serve`. Nothing is
written to the git tree: every page below lands in mkdocs-gen-files' virtual
overlay of docs_dir. The repo-root markdown files remain the single source of
truth and stay correct when read on GitHub.
"""

from __future__ import annotations

import logging
import posixpath
import re
import tomllib
from pathlib import Path

import mkdocs_gen_files
from markdown.extensions.toc import slugify as md_slugify

log = logging.getLogger(f"mkdocs.plugins.{__name__}")

REPO = Path(__file__).resolve().parent.parent
GITHUB = "https://github.com/adammatthewsteinberger/vibey-bootstrap"
BLOB = f"{GITHUB}/blob/main/"
TREE = f"{GITHUB}/tree/main/"

PAGES: dict[str, str] = {
    "README.md": "index.md",
    "docs/USAGE.md": "usage.md",
    "MIGRATING-FROM-V1.md": "MIGRATING-FROM-V1.md",
    "MIGRATING-TO-V3.md": "MIGRATING-TO-V3.md",
    "MIGRATING-TO-V4.md": "MIGRATING-TO-V4.md",
    "CHANGELOG.md": "CHANGELOG.md",
    "CONTRIBUTING.md": "CONTRIBUTING.md",
    "CLAUDE.md": "CLAUDE.md",
    "NOTICE.md": "NOTICE.md",
}

# Alembic scaffolding — no reference value.
REFERENCE_SKIP = {"vibey_bootstrap.db.migrations"}

FENCE_RE = re.compile(r"^(\s{0,3})(`{3,}|~{3,})")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
LINK_RE = re.compile(r"(?<=\]\()([^)\s]+)(?=\))")
MD_LINK_IN_TEXT_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")


def iter_lines(text: str):
    """Yield (line, in_fence) for every line, tracking ``` / ~~~ fences."""
    fence: str | None = None
    for line in text.split("\n"):
        m = FENCE_RE.match(line)
        if fence is None:
            if m:
                fence = m.group(2)
                yield line, True
                continue
            yield line, False
        else:
            if m and m.group(2)[0] == fence[0] and len(m.group(2)) >= len(fence):
                fence = None
            yield line, True


def plain(text: str) -> str:
    """Strip the inline markdown that both sluggers discard anyway."""
    text = MD_LINK_IN_TEXT_RE.sub(r"\1", text)
    return text.replace("`", "").replace("*", "").replace("_", " ")


def github_slug(text: str) -> str:
    s = plain(text).strip().lower()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    return re.sub(r"\s", "-", s)


def build_anchor_map(text: str) -> dict[str, str]:
    """{github_slug: python-markdown_slug} for every heading on the page."""
    gh_seen: dict[str, int] = {}
    md_seen: set[str] = set()
    out: dict[str, str] = {}
    for line, in_fence in iter_lines(text):
        if in_fence:
            continue
        m = HEADING_RE.match(line)
        if not m:
            continue
        raw = m.group(2)

        gh = github_slug(raw)
        n = gh_seen.get(gh, 0)
        gh_seen[gh] = n + 1
        gh_unique = gh if n == 0 else f"{gh}-{n}"

        md = md_slugify(plain(raw), "-")
        base, i = md, 1
        while md in md_seen:
            md = f"{base}_{i}"
            i += 1
        md_seen.add(md)

        out[gh_unique] = md
    return out


def translate_anchor(anchor: str, amap: dict[str, str], where: str) -> str:
    if not anchor:
        return ""
    key = anchor.lstrip("#")
    if key in amap:
        return "#" + amap[key]
    guess = re.sub(r"-{2,}", "-", key).strip("-")
    if guess != key:
        log.warning("gen_pages: %s: no heading for anchor #%s; guessing #%s", where, key, guess)
    return "#" + guess


def rewrite_target(t: str, base: str, self_map, anchors, where: str) -> str:
    if t.startswith("#"):
        return translate_anchor(t, self_map, where)

    if t.startswith(("mailto:", "http://", "https://")):
        for prefix in (BLOB, TREE):
            if t.startswith(prefix):
                rest = t[len(prefix) :]
                break
        else:
            return t  # external; untouched
        path, _, anchor = rest.partition("#")
        anchor = f"#{anchor}" if anchor else ""
    else:
        raw, _, anchor = t.partition("#")
        anchor = f"#{anchor}" if anchor else ""
        if not raw:
            return translate_anchor(anchor, self_map, where)
        path = posixpath.normpath(posixpath.join(base, raw))
        if raw.endswith("/") and not path.endswith("/"):
            path += "/"

    if path in PAGES:
        site = PAGES[path]
        return site + translate_anchor(anchor, anchors[site], where)
    if path.endswith("/"):
        return TREE + path + anchor  # GitHub slug preserved
    return BLOB + path + anchor  # GitHub slug preserved


def rewrite(text: str, base: str, self_map, anchors, where: str) -> str:
    out = []
    for line, in_fence in iter_lines(text):
        if in_fence:
            out.append(line)
        else:
            out.append(
                LINK_RE.sub(
                    lambda m: rewrite_target(m.group(0), base, self_map, anchors, where),
                    line,
                )
            )
    return "\n".join(out)


# pass 1: read + index anchors
sources: dict[str, str] = {}
anchors: dict[str, dict[str, str]] = {}
for src, site in PAGES.items():
    sources[src] = (REPO / src).read_text(encoding="utf-8")
    anchors[site] = build_anchor_map(sources[src])

# pass 2: rewrite + emit
for src, site in PAGES.items():
    base = posixpath.dirname(src)
    body = rewrite(sources[src], base, anchors[site], anchors, src)
    with mkdocs_gen_files.open(site, "w") as fd:
        fd.write(body)
    mkdocs_gen_files.set_edit_path(site, src)

# API reference, driven by [tool.setuptools] packages
with (REPO / "pyproject.toml").open("rb") as fh:
    packages = tomllib.load(fh)["tool"]["setuptools"]["packages"]

if not isinstance(packages, list):
    raise SystemExit(
        "gen_pages: [tool.setuptools] packages is not an explicit list "
        "(auto-discovery config is not supported by this script)"
    )

modules = sorted(p for p in packages if p not in REFERENCE_SKIP)

summary: list[str] = []
for dotted in modules:
    page = f"reference/{dotted}.md"
    with mkdocs_gen_files.open(page, "w") as fd:
        fd.write(f"::: {dotted}\n")
    src_path = Path(*dotted.split(".")) / "__init__.py"
    mkdocs_gen_files.set_edit_path(page, src_path.as_posix())

    depth = dotted.count(".")
    label = dotted if depth == 0 else dotted.rsplit(".", 1)[1]
    summary.append(f"{'    ' * depth}* [{label}]({dotted}.md)")

# A landing page for the section root. Without one, `reference/` is a pure
# literate-nav section: every leaf resolves but /reference/ itself 404s, and
# README links to exactly that URL.
index_lines = [
    "# API Reference",
    "",
    "Generated from the package docstrings and signatures by",
    "[mkdocstrings](https://mkdocstrings.github.io/), one page per package in",
    "`[tool.setuptools] packages` — so a new subpackage appears here as soon as",
    "it is declared for distribution.",
    "",
    f"{len(modules)} packages:",
    "",
]
index_lines += [f"- [`{dotted}`]({dotted}.md)" for dotted in modules]

with mkdocs_gen_files.open("reference/index.md", "w") as fd:
    fd.write("\n".join(index_lines) + "\n")
mkdocs_gen_files.set_edit_path("reference/index.md", "docs/gen_pages.py")

with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as fd:
    fd.write("* [Overview](index.md)\n" + "\n".join(summary) + "\n")
