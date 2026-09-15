# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The governance corpus index (#249): determinism, integrity, and loud drift."""

from __future__ import annotations

from pathlib import Path

from vibey_gh import corpus
from vibey_gh.cli import main
from vibey_gh.config import GhConfig


def _law(tmp_path: Path) -> GhConfig:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "doctrines.md").write_text(
        "# The Twelve\n\npreamble text\n\n## 1 — BLUF\n\nthe problem first\n\n"
        "## 2 — Channels\n\nbeginner then engineer\n",
        encoding="utf-8",
    )
    (docs / "constitution.md").write_text(
        "# The Constitution\n\n## Article I\n\nthe order\n", encoding="utf-8"
    )
    (docs / "sd-01-counterparties.md").write_text(
        "# SD-01\n\nverbatim standing text\n", encoding="utf-8"
    )
    return GhConfig(root=tmp_path)


def test_the_index_is_deterministic_byte_for_byte(tmp_path: Path):
    cfg = _law(tmp_path)
    first = corpus.write(cfg).read_bytes()
    second = corpus.write(cfg).read_bytes()
    assert first == second


def test_chunks_carry_document_anchor_and_hash(tmp_path: Path):
    cfg = _law(tmp_path)
    index = corpus.build(cfg)
    anchors = {(c["document"], c["anchor"]) for c in index["chunks"]}
    assert ("docs/doctrines.md", "1 — BLUF") in anchors
    assert ("docs/constitution.md", "Article I") in anchors
    assert ("docs/sd-01-counterparties.md", "SD-01") in anchors
    assert all(len(c["sha256"]) == 64 for c in index["chunks"])
    # missing documents are simply absent, never invented
    assert "docs/commandments.md" not in index["documents"]


def test_one_hash_walk_detects_any_drift(tmp_path: Path):
    cfg = _law(tmp_path)
    corpus.write(cfg)
    ok, message = corpus.check(cfg)
    assert ok and "intact" in message

    law = tmp_path / "docs" / "constitution.md"
    law.write_text(law.read_text(encoding="utf-8") + "\ntampered\n", encoding="utf-8")
    ok, message = corpus.check(cfg)
    assert not ok and "corpus drift" in message and "regenerate" in message


def test_missing_or_garbled_index_fails_loudly(tmp_path: Path):
    cfg = _law(tmp_path)
    ok, message = corpus.check(cfg)
    assert not ok and "law but no index" in message
    (tmp_path / "corpus-index.json").write_text("not json", encoding="utf-8")
    ok, message = corpus.check(cfg)
    assert not ok and "not valid JSON" in message


def test_cli_builds_and_checks(tmp_path: Path, monkeypatch, capsys):
    _law(tmp_path)
    (tmp_path / ".vibey-gh.toml").write_text("", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert main(["corpus-index"]) == 0
    out = capsys.readouterr().out
    assert "chunk(s)" in out and "corpus" in out
    assert main(["corpus-index", "--check"]) == 0
    (tmp_path / "docs" / "doctrines.md").write_text("# changed\n\nlaw moved\n", encoding="utf-8")
    assert main(["corpus-index", "--check"]) == 1
    assert "corpus drift" in capsys.readouterr().err


def test_overlapping_patterns_never_duplicate_a_document(tmp_path: Path, monkeypatch):
    """The dedupe guard: if a future pattern edit makes two entries match one file,
    the document indexes once, in constitutional order."""
    cfg = _law(tmp_path)
    monkeypatch.setattr(corpus, "CORPUS_DOCUMENTS", ("docs/constitution.md", "docs/const*.md"))
    index = corpus.build(cfg)
    assert index["documents"].count("docs/constitution.md") == 1


def test_the_configured_source_and_index_path_are_honoured(tmp_path: Path):
    """`[documentation] governance_source` and `corpus_index` drive the command, and the
    index records paths relative to itself, so indexing the same corpus from a monorepo
    root and from the package's own root writes identical bytes to the same file."""
    from vibey_gh.config import DocumentationConfig

    package = tmp_path / "src" / "tools" / "gh"
    package.mkdir(parents=True)
    _law(package)
    from_package = corpus.write(GhConfig(root=package)).read_bytes()
    root_cfg = GhConfig(
        root=tmp_path,
        documentation=DocumentationConfig(
            governance_source="src/tools/gh/docs", corpus_index="src/tools/gh/corpus-index.json"
        ),
    )
    target = corpus.write(root_cfg)
    assert target == package / "corpus-index.json"
    assert target.read_bytes() == from_package
    assert corpus.index_path(root_cfg) == target
    assert corpus.check(root_cfg)[0]
    assert '"docs/doctrines.md"' in target.read_text(encoding="utf-8")
    (package / "docs" / "doctrines.md").write_text("# changed\n", encoding="utf-8")
    ok, message = corpus.check(root_cfg)
    assert not ok and "corpus drift" in message
