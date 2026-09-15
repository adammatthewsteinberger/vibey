# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Hermetic coverage for the lexical context engine walking skeleton."""

from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from vibey_skills.context_engine import (
    ContextEngineError,
    build_index,
    build_manifest,
    compile_packet,
    estimate_tokens,
    inspect_index,
    search,
    validate_request,
)


def _skill(
    root: Path,
    plugin: str,
    name: str,
    *,
    description: str = "Use when testing PostgreSQL with pytest.",
    metadata: str = "",
    body: str = "## Procedure\n\nRun pytest safely.\n",
) -> Path:
    path = root / plugin / "skills" / name / "SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        f"---\nname: {name}\ndescription: {description}\n{metadata}---\n\n# {name}\n\n{body}",
        encoding="utf-8",
    )
    return path


class ContextEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.plugins = self.base / "plugins"
        _skill(
            self.plugins,
            "quality-engineering",
            "python-quality-testing",
            metadata=(
                "domains:\n  - testing\nphases:\n  - build\nlanguages:\n  - python\n"
                "technologies:\n  - postgresql\nmandatory_sections:\n  - Safety\n"
                "retrieval_version: 1\n"
            ),
            body=(
                "## Safety\n\nUse an isolated PostgreSQL test database.\n\n"
                "## pytest xdist\n\nGive each worker a separate schema and close async processes.\n"
            ),
        )
        _skill(
            self.plugins,
            "frontend",
            "css-layout",
            description="Use when implementing CSS grid layouts.",
            body="## Grid\n\nUse CSS grid for page layout.\n",
        )
        self.index = self.base / "index"
        build_index(self.index, self.plugins)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_manifest_is_deterministic_and_has_exact_ranges(self) -> None:
        first = build_manifest(self.plugins)
        second = build_manifest(self.plugins)
        self.assertEqual(first, second)
        self.assertEqual(len(first["skills"]), 2)
        chunk = next(item for item in first["chunks"] if item["heading"] == "Safety")
        source = (self.base / chunk["source_path"]).read_text(encoding="utf-8").splitlines()
        recovered = "\n".join(source[chunk["line_start"] - 1 : chunk["line_end"]])
        self.assertIn("isolated PostgreSQL", recovered)

    def test_duplicate_skill_names_fail_closed(self) -> None:
        _skill(self.plugins, "another", "python-quality-testing")
        with self.assertRaisesRegex(ContextEngineError, "duplicate skill name"):
            build_manifest(self.plugins)

    def test_missing_mandatory_heading_fails_closed(self) -> None:
        path = self.plugins / "quality-engineering/skills/python-quality-testing/SKILL.md"
        path.write_text(path.read_text().replace("  - Safety", "  - Does Not Exist"))
        with self.assertRaisesRegex(ContextEngineError, "missing mandatory heading"):
            build_manifest(self.plugins)

    def test_rebuild_has_same_digest_and_chunk_ids(self) -> None:
        one = build_index(self.base / "one", self.plugins)
        two = build_index(self.base / "two", self.plugins)
        self.assertEqual(one["corpus_sha256"], two["corpus_sha256"])
        self.assertEqual([c["id"] for c in one["chunks"]], [c["id"] for c in two["chunks"]])

    def test_search_is_parameterized_filtered_and_deterministic(self) -> None:
        query = {
            "objective": 'pytest postgres" OR 1=1; DROP TABLE chunks; --',
            "phase": "build",
            "languages": ["python"],
            "excluded_plugins": ["frontend"],
        }
        first = search(self.index, query)
        second = search(self.index, query)
        self.assertEqual(first, second)
        self.assertTrue(first)
        self.assertEqual({item["plugin"] for item in first}, {"quality-engineering"})
        with sqlite3.connect(self.index / "index.sqlite3") as connection:
            self.assertEqual(connection.execute("SELECT count(*) FROM chunks").fetchone()[0], 5)

    def test_explicit_skill_activation_precedes_lexical_search(self) -> None:
        results = search(
            self.index,
            {"objective": "unrelated words", "required_skills": ["python-quality-testing"]},
        )
        self.assertTrue(results)
        self.assertEqual({item["skill"] for item in results}, {"python-quality-testing"})
        self.assertIn("required_skill", results[0]["reasons"])

    def test_retrieval_metadata_contributes_searchable_signals(self) -> None:
        results = search(self.index, {"objective": "testing", "phase": "build"})
        self.assertTrue(results)
        self.assertEqual(results[0]["skill"], "python-quality-testing")
        self.assertIn("signal:build", results[0]["reasons"])

    def test_packet_includes_mandatory_provenance_and_honors_budget(self) -> None:
        request = {
            "title": "PostgreSQL pytest-xdist isolation",
            "objective": "test a PostgreSQL service in parallel",
            "phase": "build",
            "languages": ["python"],
            "commands": ["pytest -n auto"],
            "required_skills": ["python-quality-testing"],
        }
        markdown, packet = compile_packet(self.index, request, budget=1_000)
        self.assertEqual(packet["status"], "ok")
        self.assertIn("Use an isolated PostgreSQL test database", markdown)
        self.assertNotIn("CSS grid", markdown)
        self.assertLessEqual(estimate_tokens(markdown), 1_000)
        included = packet["included_chunks"]
        self.assertTrue(all(item["source_path"] and item["line_start"] for item in included))
        self.assertTrue(all(item["content_sha256"] and item["reasons"] for item in included))
        self.assertEqual(
            packet["packet_sha256"], __import__("hashlib").sha256(markdown.encode()).hexdigest()
        )

    def test_budget_insufficient_never_truncates_mandatory_text(self) -> None:
        path = self.plugins / "quality-engineering/skills/python-quality-testing/SKILL.md"
        text = path.read_text().replace(
            "Use an isolated PostgreSQL test database.", "mandatory " * 5_000
        )
        path.write_text(text)
        build_index(self.index, self.plugins)
        markdown, packet = compile_packet(
            self.index,
            {"objective": "postgres", "required_skills": ["python-quality-testing"]},
            budget=1_000,
        )
        self.assertEqual(markdown, "")
        self.assertEqual(packet["status"], "budget_insufficient")

    def test_low_confidence_requests_full_skill_fallback(self) -> None:
        markdown, packet = compile_packet(self.index, {"objective": "zzzz-no-match"})
        self.assertEqual(markdown, "")
        self.assertEqual(packet["status"], "low_confidence")
        self.assertEqual(packet["fallback"], "activate_full_native_skills")

    def test_request_validation_rejects_unknowns_and_redacts_secrets(self) -> None:
        with self.assertRaisesRegex(ContextEngineError, "unknown request"):
            validate_request({"objective": "x", "surprise": True})
        clean = validate_request(
            {"objective": "API_KEY=super-secret-value", "error_summary": "ghp_abcdefghijk"}
        )
        self.assertNotIn("super-secret-value", json.dumps(clean))
        self.assertNotIn("ghp_abcdefghijk", json.dumps(clean))

    def test_corrupt_manifest_and_symlink_index_fail_closed(self) -> None:
        manifest = self.index / "manifest.json"
        data = json.loads(manifest.read_text())
        data["chunks"][0]["text"] = "tampered"
        manifest.write_text(json.dumps(data))
        with self.assertRaisesRegex(ContextEngineError, "digest mismatch"):
            inspect_index(self.index)
        link = self.base / "linked-index"
        link.symlink_to(self.index, target_is_directory=True)
        with self.assertRaisesRegex(ContextEngineError, "symlink"):
            build_index(link, self.plugins)


if __name__ == "__main__":
    unittest.main()
