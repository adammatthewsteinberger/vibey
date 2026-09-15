# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Comprehensive documentation configuration and deterministic contracts."""

import json
from pathlib import Path

import pytest

from vibey_gh.config import (
    DEFAULT_DOCUMENTATION_FILES,
    DocumentationConfig,
    GhConfig,
    load_config,
)
from vibey_gh.documentation import check


def test_documentation_can_be_disabled(tmp_path: Path):
    assert check(GhConfig(root=tmp_path, documentation=DocumentationConfig(enabled=False))).ok


def test_documentation_reports_missing_empty_invalid_and_provenance(tmp_path: Path):
    required = ("README.md", "docs/index.md", ".claude/settings.json", "EMPTY.md", "MISSING.md")
    (tmp_path / "docs").mkdir()
    (tmp_path / ".claude").mkdir()
    (tmp_path / "README.md").write_text("plain")
    (tmp_path / "docs/index.md").write_text("plain")
    (tmp_path / ".claude/settings.json").write_text("[]")
    (tmp_path / "EMPTY.md").write_text("")
    policy = DocumentationConfig(required_files=required, require_provenance=True)
    report = check(GhConfig(root=tmp_path, documentation=policy))
    assert "MISSING.md is missing" in report.problems
    assert "EMPTY.md is empty" in report.problems
    assert ".claude/settings.json must contain a JSON object" in report.problems
    assert "README.md has no Vibey provenance" in report.problems
    assert "docs/index.md has no Vibey provenance" in report.problems
    (tmp_path / ".claude/settings.json").write_text("{")
    assert (
        ".claude/settings.json is invalid JSON"
        in check(GhConfig(root=tmp_path, documentation=policy)).problems
    )


def test_an_adopter_documents_its_own_product_not_this_tool(tmp_path: Path):
    """The line between what every managed repository owes and what only this one does.

    The agent-docs layout is owed by everyone: those files describe the ADOPTER's project
    and make it navigable to an agent. What is *inside* them is the adopter's own subject —
    no `## Why vibey-gh` heading, no branded provenance sentence, no architecture surfaces
    named after this tool's modules.
    """
    for relative in DEFAULT_DOCUMENTATION_FILES:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("about my own product\n", encoding="utf-8")
    (tmp_path / ".claude/settings.json").write_text("{}", encoding="utf-8")
    (tmp_path / ".claude-plugin/marketplace.json").write_text('{"plugins": []}', encoding="utf-8")
    report = check(GhConfig(root=tmp_path))

    # The layout is satisfied, so nothing is reported missing...
    assert not any(problem.endswith("is missing") for problem in report.problems)
    # ...and none of this project's own narrative is demanded of theirs.
    for imposed in ("Why vibey-gh", "provenance sentence", "project surface", "at least"):
        assert not any(imposed in problem for problem in report.problems), imposed


def test_every_required_file_is_required_individually(tmp_path: Path):
    """A list of required files is an AND: having one never excuses another."""
    (tmp_path / ".agents/skills").mkdir(parents=True)
    (tmp_path / ".agents/skills/README.md").write_text("skills")
    problems = check(GhConfig(root=tmp_path)).problems
    assert not any(".agents/skills/README.md is missing" in p for p in problems)
    assert any(".claude-plugin/marketplace.json is missing" in p for p in problems)
    assert sum(p.endswith("is missing") for p in problems) == len(DEFAULT_DOCUMENTATION_FILES) - 1


def test_a_repository_can_require_its_own_readme_sections(tmp_path: Path):
    """The requirement is the repository's own words, not this project's headings."""
    (tmp_path / "README.md").write_text("# My product\n\n## Install\n\nRun it.\n")
    report = check(
        GhConfig(
            root=tmp_path,
            documentation=DocumentationConfig(
                readme_sections=("## Install", "## Support", "## Licence")
            ),
        )
    )
    assert "README.md is missing human documentation section: ## Support" in report.problems
    assert "README.md is missing human documentation section: ## Licence" in report.problems
    assert not any("## Install" in problem for problem in report.problems)


@pytest.mark.parametrize("field", ["automation_doc_min_words", "mermaid_min_edges"])
def test_a_negative_documentation_threshold_is_rejected(field):
    with pytest.raises(ValueError, match="must not be negative"):
        DocumentationConfig(**{field: -1})


def test_documentation_rejects_incomplete_mermaid_project_map(tmp_path: Path):
    diagram = tmp_path / "docs/project.mmd"
    diagram.parent.mkdir()
    diagram.write_text("flowchart TB\n  CLI --> API\n")
    report = check(
        GhConfig(
            root=tmp_path,
            documentation=DocumentationConfig(
                required_files=("docs/project.mmd",),
                mermaid_terms=("flowchart", "CLI", "API", "Provenance", "Realign"),
                mermaid_min_edges=20,
            ),
        )
    )
    assert any("missing required project surface" in problem for problem in report.problems)
    assert any("not comprehensive enough" in problem for problem in report.problems)


def test_documentation_rejects_placeholder_github_automation_guide(tmp_path: Path):
    sections = ("## Delivery model", "## Workflow inventory", "## Failure recovery")
    guide = tmp_path / ".github/AUTOMATION.md"
    guide.parent.mkdir()
    guide.write_text("# GitHub automation\n\nSee docs/workflows.md.\n")
    report = check(
        GhConfig(
            root=tmp_path,
            documentation=DocumentationConfig(
                required_files=(".github/AUTOMATION.md",),
                automation_doc_sections=sections,
                automation_doc_min_words=500,
                require_provenance=True,
            ),
        )
    )
    for heading in sections:
        assert any(heading in problem for problem in report.problems)
    assert any("at least 500 words" in problem for problem in report.problems)
    assert any("exact Vibey provenance" in problem for problem in report.problems)


def test_documentation_validates_and_loads_configuration(tmp_path: Path):
    (tmp_path / ".vibey-gh.toml").write_text(
        '[documentation]\nmodel="opus"\nrequired_files=["README.md"]\n'
        'production_label="Stable"\npreview_label="Next"\nproduction_indexing=false\n'
        "preview_indexing=true\ngenerate_robots=false\ngenerate_sitemap_index=false\n"
        "generate_llms_txt=false\ngenerate_llms_full_txt=false\ngenerate_json_ld=false\n"
        'author_name="Maintainer"\nauthor_url="https://example.test"\n'
        'google_analytics_id="G-ABC1234567"\n'
    )
    value = load_config(tmp_path).documentation
    assert value.model == "opus"
    assert value.required_files == ("README.md",)
    assert value.production_label == "Stable" and value.preview_label == "Next"
    assert not value.production_indexing and value.preview_indexing
    assert not value.generate_robots and not value.generate_sitemap_index
    assert not value.generate_llms_txt and not value.generate_llms_full_txt
    assert not value.generate_json_ld
    assert value.author_name == "Maintainer" and value.author_url == "https://example.test"
    assert value.google_analytics_id == "G-ABC1234567"


def test_documentation_google_analytics_defaults_to_disabled(tmp_path: Path):
    assert load_config(tmp_path).documentation.google_analytics_id == ""


@pytest.mark.parametrize("value", ["G-ABC1234567", "G-0"])
def test_documentation_accepts_valid_google_analytics_ids(value: str):
    assert DocumentationConfig(google_analytics_id=value).google_analytics_id == value


@pytest.mark.parametrize("value", ["UA-12345-1", "g-abc1234567", "G-", "G-ABC 123", " G-ABC123"])
def test_documentation_rejects_malformed_google_analytics_ids(value: str):
    with pytest.raises(ValueError):
        DocumentationConfig(google_analytics_id=value)


def test_the_living_roadmap_is_part_of_the_contract(tmp_path: Path):
    """The living-roadmap doctrine (vibey-gh#211): a project keeps an active roadmap
    until its goal is reached AND its humans declare it done. The deterministic
    contract enforces presence — docs/roadmap.md or ROADMAP.md, non-empty — and the
    exact-head review judges liveness. Opting out silences only the presence check."""
    cfg = GhConfig(root=tmp_path, documentation=DocumentationConfig(required_files=()))
    assert any("no living roadmap" in problem for problem in check(cfg).problems)

    (tmp_path / "ROADMAP.md").write_text("# Goal\nShip it, then the humans decide.")
    assert check(cfg).ok

    (tmp_path / "ROADMAP.md").write_text("   \n")
    assert any("no living roadmap" in problem for problem in check(cfg).problems)

    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/roadmap.md").write_text("# Goal\nAlive at the canonical path.")
    assert check(cfg).ok


def test_the_roadmap_requirement_can_be_declined_deliberately(tmp_path: Path):
    policy = DocumentationConfig(required_files=(), require_roadmap=False)
    assert check(GhConfig(root=tmp_path, documentation=policy)).ok


def test_require_roadmap_loads_from_toml(tmp_path: Path):
    (tmp_path / ".vibey-gh.toml").write_text("[documentation]\nrequire_roadmap = false\n")
    assert load_config(tmp_path).documentation.require_roadmap is False
    (tmp_path / ".vibey-gh.toml").write_text("[documentation]\n")
    assert load_config(tmp_path).documentation.require_roadmap is True


def test_documentation_validates_complete_marketplace_shape(tmp_path: Path):
    marketplace = tmp_path / ".claude-plugin/marketplace.json"
    marketplace.parent.mkdir()
    required = (".claude-plugin/marketplace.json",)
    cfg = GhConfig(root=tmp_path, documentation=DocumentationConfig(required_files=required))
    marketplace.write_text("{")
    assert "marketplace.json is invalid JSON" in check(cfg).problems[0]
    marketplace.write_text('{"plugins":[]}')
    assert "has no plugins" in check(cfg).problems[0]
    marketplace.write_text('{"plugins":[null,{"source":"../bad"},{"source":"./plugins/one"}]}')
    problems = check(cfg).problems
    assert any("unsafe source" in problem for problem in problems)
    assert any("plugin.json is missing" in problem for problem in problems)
    assert any("has no skills" in problem for problem in problems)


def test_documentation_treats_repo_root_source_as_safe(tmp_path: Path):
    marketplace = tmp_path / ".claude-plugin/marketplace.json"
    marketplace.parent.mkdir()
    required = (".claude-plugin/marketplace.json",)
    cfg = GhConfig(root=tmp_path, documentation=DocumentationConfig(required_files=required))
    marketplace.write_text('{"plugins":[{"source":"."}]}')
    problems = check(cfg).problems
    assert not any("unsafe source" in problem for problem in problems)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"required_files": ("../outside",)},
        {"required_files": ("/absolute",)},
        {"model": ""},
        {"production_label": " "},
        {"preview_label": ""},
        {"author_name": ""},
        {"author_url": ""},
    ],
)
def test_documentation_rejects_unsafe_or_empty_configuration(kwargs):
    with pytest.raises(ValueError):
        DocumentationConfig(**kwargs)


def test_this_repository_documentation_contract_is_complete():
    root = Path(__file__).resolve().parent.parent
    cfg = load_config(root)
    report = check(cfg)
    assert report.ok, report.problems
    # `report.ok` says something only if this repository actually declares a contract for
    # `check` to enforce. Every narrative field defaults to empty — that is the point, for
    # an adopter — so dropping one from `.vibey-gh.toml` would leave the assertion above
    # passing vacuously instead of failing. These pin the declaration, not the prose.
    doc = cfg.documentation
    assert doc.require_provenance
    assert doc.readme_sections and doc.automation_doc_sections and doc.mermaid_terms
    assert doc.automation_doc_min_words >= 500
    assert doc.mermaid_min_edges >= 20
    marketplace = json.loads((root / ".claude-plugin/marketplace.json").read_text())
    assert len(marketplace["plugins"]) >= 4
    for plugin in marketplace["plugins"]:
        path = root / plugin["source"]
        assert (path / ".claude-plugin/plugin.json").is_file()
        assert list((path / "skills").glob("*/SKILL.md"))


def test_the_required_automation_doc_is_not_a_name_github_hijacks():
    """`.github/README.md` is not a neutral filename — it is the repository's front page.

    GitHub resolves a repository's landing README as `.github/README.md` first, and the
    root `README.md` only if that is absent. Requiring the former therefore replaced every
    adopting repository's *product* README with maintainer-facing automation notes, on the
    page a user lands on. Both this project and its first adopter were serving the wrong
    document, and nothing written inside the file could change that: the name is what
    GitHub reads.

    This is the same principle issue #82 settled — an adopter documents their product, and
    this tool does not get to reshape that — arriving through a filename instead of a
    heading.
    """
    from vibey_gh.config import DEFAULT_AUTOMATION_DOC, DEFAULT_DOCUMENTATION_FILES

    hijacking = {".github/README.md", ".github/readme.md"}
    assert DEFAULT_AUTOMATION_DOC not in hijacking
    displaced = hijacking & set(DEFAULT_DOCUMENTATION_FILES)
    assert not displaced, f"{displaced} would displace the adopter's own landing README"
    # The root README must still be required: it is the product-facing document, and the
    # whole point is that it is the one GitHub shows.
    assert "README.md" in DEFAULT_DOCUMENTATION_FILES
