# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Deterministic documentation contract checks used locally and before AI maintenance."""

from __future__ import annotations

import json
from dataclasses import dataclass

from vibey_gh.config import GhConfig

README_PROVENANCE = (
    "Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), "
    "Developed by [Adam Matthew Steinberger]"
    "(https://vibewithadam.matthewsteinberger.com/) "
    "([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/))."
)


@dataclass(frozen=True)
class DocumentationReport:
    problems: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.problems


def check(cfg: GhConfig) -> DocumentationReport:
    if not cfg.documentation.enabled:
        return DocumentationReport(())
    problems: list[str] = []
    for relative in cfg.documentation.required_files:
        path = cfg.root / relative
        if not path.is_file():
            problems.append(f"{relative} is missing")
        elif not path.read_text(encoding="utf-8").strip():
            problems.append(f"{relative} is empty")
    settings = cfg.root / ".claude/settings.json"
    if settings.is_file():
        try:
            value = json.loads(settings.read_text(encoding="utf-8"))
            if not isinstance(value, dict):
                problems.append(".claude/settings.json must contain a JSON object")
        except json.JSONDecodeError:
            problems.append(".claude/settings.json is invalid JSON")
    marketplace = cfg.root / ".claude-plugin/marketplace.json"
    if marketplace.is_file():
        try:
            value = json.loads(marketplace.read_text(encoding="utf-8"))
            plugins = value.get("plugins", []) if isinstance(value, dict) else []
            if not plugins:
                problems.append(".claude-plugin/marketplace.json has no plugins")
            for plugin in plugins:
                source = plugin.get("source", "") if isinstance(plugin, dict) else ""
                root = (cfg.root / source).resolve()
                repo_root = cfg.root.resolve()
                if not source or (root != repo_root and repo_root not in root.parents):
                    problems.append(f"marketplace plugin has unsafe source: {source!r}")
                    continue
                if not (root / ".claude-plugin/plugin.json").is_file():
                    problems.append(f"{source}/.claude-plugin/plugin.json is missing")
                if not list((root / "skills").glob("*/SKILL.md")):
                    problems.append(f"{source} has no skills")
        except json.JSONDecodeError:
            problems.append(".claude-plugin/marketplace.json is invalid JSON")
    if cfg.documentation.require_roadmap:
        roadmaps = ("docs/roadmap.md", "ROADMAP.md")
        if not any(
            (cfg.root / rel).is_file() and (cfg.root / rel).read_text(encoding="utf-8").strip()
            for rel in roadmaps
        ):
            problems.append(
                "no living roadmap: docs/roadmap.md or ROADMAP.md must exist and be non-empty"
                " until the project's goal is reached and its humans declare it done"
                " (set documentation.require_roadmap = false to silence the deterministic"
                " check; the exact-head review still judges liveness)"
            )
    # Everything below is what THIS repository asks of its own documentation. A project
    # that installs vibey-gh documents its own product, not this tool's internals, so each
    # requirement is empty until the repository declares it in `.vibey-gh.toml`.
    if cfg.documentation.require_provenance:
        for relative in cfg.documentation.provenance_files:
            path = cfg.root / relative
            if path.is_file() and "Made with" not in path.read_text(encoding="utf-8"):
                problems.append(f"{relative} has no Vibey provenance")

    readme = cfg.root / "README.md"
    if readme.is_file() and (
        cfg.documentation.readme_sections or cfg.documentation.require_provenance
    ):
        text = readme.read_text(encoding="utf-8")
        for heading in cfg.documentation.readme_sections:
            if heading not in text:
                problems.append(f"README.md is missing human documentation section: {heading}")
        if cfg.documentation.require_provenance and not text.rstrip().endswith(README_PROVENANCE):
            problems.append("README.md must end with the exact Vibey provenance sentence")

    automation_doc = cfg.root / cfg.documentation.automation_doc
    if automation_doc.is_file() and (
        cfg.documentation.automation_doc_sections
        or cfg.documentation.automation_doc_min_words
        or cfg.documentation.require_provenance
    ):
        text = automation_doc.read_text(encoding="utf-8")
        for heading in cfg.documentation.automation_doc_sections:
            if heading not in text:
                problems.append(
                    f"{cfg.documentation.automation_doc} is missing automation section: {heading}"
                )
        minimum = cfg.documentation.automation_doc_min_words
        if minimum and len(text.split()) < minimum:
            problems.append(
                f"{cfg.documentation.automation_doc} is not comprehensive enough: "
                f"expected at least {minimum} words"
            )
        if cfg.documentation.require_provenance and not text.rstrip().endswith(README_PROVENANCE):
            problems.append(
                f"{cfg.documentation.automation_doc} must end with the exact Vibey provenance sentence"
            )

    diagram = cfg.root / "docs/project.mmd"
    if diagram.is_file() and (
        cfg.documentation.mermaid_terms or cfg.documentation.mermaid_min_edges
    ):
        text = diagram.read_text(encoding="utf-8")
        for term in cfg.documentation.mermaid_terms:
            if term not in text:
                problems.append(f"docs/project.mmd is missing required project surface: {term}")
        edges = cfg.documentation.mermaid_min_edges
        if edges and text.count("-->") < edges:
            problems.append(
                f"docs/project.mmd is not comprehensive enough: expected at least {edges} edges"
            )
    return DocumentationReport(tuple(problems))
