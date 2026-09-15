# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""CLI and process-contract tests for retrieval packet generation."""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_context_engine import _skill

from vibey_skills.cli import main


class ContextCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.plugins = self.root / "plugins"
        _skill(
            self.plugins,
            "quality-engineering",
            "python-quality-testing",
            metadata="mandatory_sections:\n  - Safety\nretrieval_version: 1\n",
            body=(
                "## Safety\n\nUse isolated PostgreSQL databases.\n\n"
                "## Parallel tests\n\nAssign one schema to every pytest-xdist worker.\n"
            ),
        )
        self.index = self.root / "index"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_cli(self, args: list[str]) -> tuple[int, str, str]:
        stdout, stderr = io.StringIO(), io.StringIO()
        with (
            patch("vibey_skills.context_engine.plugins_root", return_value=self.plugins),
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            code = main(args)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_json_cli_and_packet_process_contract(self) -> None:
        code, stdout, stderr = self.run_cli(["index", "build", "--output", str(self.index)])
        self.assertEqual((code, stderr), (0, ""))
        self.assertEqual(json.loads(stdout)["skill_count"], 1)

        code, stdout, stderr = self.run_cli(
            ["search", "postgres pytest", "--index", str(self.index), "--json"]
        )
        self.assertEqual((code, stderr), (0, ""))
        self.assertEqual(json.loads(stdout)[0]["skill"], "python-quality-testing")

        request = self.root / "request.json"
        packet = self.root / "packet.md"
        provenance = self.root / "packet.json"
        request.write_text(
            json.dumps(
                {
                    "objective": "parallel PostgreSQL tests",
                    "required_skills": ["python-quality-testing"],
                }
            ),
            encoding="utf-8",
        )
        code, stdout, stderr = self.run_cli(
            [
                "packet",
                "--request",
                str(request),
                "--index",
                str(self.index),
                "--budget",
                "1000",
                "--output",
                str(packet),
                "--manifest",
                str(provenance),
            ]
        )
        self.assertEqual((code, stdout, stderr), (0, "", ""))
        self.assertIn("pytest-xdist", packet.read_text(encoding="utf-8"))
        result = json.loads(provenance.read_text(encoding="utf-8"))
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["included_chunks"][0]["reasons"], ["mandatory_section"])

    def test_cli_errors_use_stderr(self) -> None:
        code, stdout, stderr = self.run_cli(
            ["search", "query", "--index", str(self.root / "missing"), "--json"]
        )
        self.assertEqual(code, 1)
        self.assertEqual(stdout, "")
        self.assertIn("index directory does not exist", stderr)


if __name__ == "__main__":
    unittest.main()
