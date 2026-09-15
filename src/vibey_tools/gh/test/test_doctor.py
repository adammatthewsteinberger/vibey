# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The doctor: will the automation actually work?

Each test encodes one adoption failure that cost real debugging on a live repository.
"""

from __future__ import annotations

from pathlib import Path

from vibey_gh import doctor
from vibey_gh.cli import main
from vibey_gh.config import DEFAULT_SUPERSEDED_TEXTS, GhConfig


def _repo(tmp_path: Path, toml: str = "") -> Path:
    (tmp_path / ".vibey-gh.toml").write_text(toml)
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    return tmp_path


def test_a_key_in_the_wrong_section_is_named(tmp_path):
    """The near-miss this encodes: a GA id inserted under a comment that merely mentioned
    [documentation] — silently ignored, GA_ID rendered empty, every check green."""
    _repo(tmp_path, '[install]\ngoogle_analytics_id = "G-XXXX"\npin_version = true\n')
    findings = doctor.diagnose(root=tmp_path)
    assert any("google_analytics_id" in f.message and f.severity == "error" for f in findings)


def test_an_unknown_section_is_named(tmp_path):
    _repo(tmp_path, "[documentaton]\nenabled = true\n")
    findings = doctor.diagnose(root=tmp_path)
    assert any("[documentaton] is not a section" in f.message for f in findings)


def test_nested_fallback_keys_are_checked(tmp_path):
    _repo(tmp_path, '[pr_automation.fallback]\nrunner = "x"\n')
    findings = doctor.diagnose(root=tmp_path)
    assert any("pr_automation.fallback] runner is not a key" in f.message for f in findings)


def test_enabled_gate_without_the_workflow_is_the_stuck_train(tmp_path):
    """pr_automation.enabled defaults true; without pr-automation.yml the merge train
    refuses every pull request — green, mergeable, stuck forever."""
    _repo(tmp_path)
    findings = doctor.diagnose(root=tmp_path)
    assert any("merge train will refuse every pull request" in f.message for f in findings)
    (tmp_path / ".github" / "workflows" / "pr-automation.yml").write_text("name: PR automation\n")
    assert not any("merge train" in f.message for f in doctor.diagnose(root=tmp_path))


def test_ruff_selecting_e_collides_with_the_header(tmp_path):
    _repo(tmp_path, "[pr_automation]\nenabled = false\n")
    (tmp_path / "pyproject.toml").write_text(
        '[tool.ruff]\nline-length = 100\n[tool.ruff.lint]\nselect = ["E", "F"]\n'
    )
    findings = doctor.diagnose(root=tmp_path)
    assert any("fails E501" in f.message for f in findings)
    (tmp_path / "pyproject.toml").write_text(
        '[tool.ruff]\nline-length = 100\n[tool.ruff.lint]\nselect = ["E"]\nignore = ["E501"]\n'
    )
    assert not any("E501" in f.message for f in doctor.diagnose(root=tmp_path))


def test_two_pages_deployers_contend(tmp_path):
    _repo(tmp_path, "[pr_automation]\nenabled = false\n")
    wf = tmp_path / ".github" / "workflows"
    (wf / "docs.yml").write_text("uses: actions/deploy-pages@v4\n")
    (wf / "release-surfaces.yml").write_text("uses: actions/deploy-pages@v4\n")
    findings = doctor.diagnose(root=tmp_path)
    assert any("contend for the same site" in f.message for f in findings)


def test_superseded_headers_are_a_warning(tmp_path):
    _repo(tmp_path, '[pr_automation]\nenabled = false\n[fingerprint]\nsources = ["src/*.py"]\n')
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "old.py").write_text(f"# {DEFAULT_SUPERSEDED_TEXTS[1]}\nx = 1\n")
    findings = doctor.diagnose(root=tmp_path)
    assert any(f.severity == "warning" and "superseded" in f.message for f in findings)


def test_a_healthy_repo_is_clean_and_the_cli_says_so(tmp_path, capsys, monkeypatch):
    _repo(tmp_path, "[pr_automation]\nenabled = false\n")
    monkeypatch.chdir(tmp_path)
    assert main(["doctor"]) == 0
    assert "should function" in capsys.readouterr().out


def test_the_cli_exits_nonzero_on_errors(tmp_path, capsys, monkeypatch):
    _repo(tmp_path)  # enabled-by-default gate, no workflow
    monkeypatch.chdir(tmp_path)
    assert main(["doctor"]) == 1
    assert "problem(s) that will break the automation" in capsys.readouterr().err


def test_free_form_rulesets_and_dogfood_config_stay_clean(tmp_path):
    """[rulesets] is per-branch free-form; and this repository's own maximal config must
    diagnose clean, or the key maps have drifted from the loader."""
    assert doctor.diagnose(root=Path(__file__).resolve().parent.parent) == []
    _repo(tmp_path, '[rulesets."develop"]\nanything = true\n[pr_automation]\nenabled = false\n')
    assert doctor.diagnose(root=tmp_path) == []


def test_the_cli_reports_warnings_without_failing(tmp_path, capsys, monkeypatch):
    from vibey_gh.config import DEFAULT_SUPERSEDED_TEXTS as OLD

    _repo(tmp_path, '[pr_automation]\nenabled = false\n[fingerprint]\nsources = ["src/*.py"]\n')
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "old.py").write_text(f"# {OLD[1]}\nx = 1\n")
    monkeypatch.chdir(tmp_path)
    assert main(["doctor"]) == 0
    assert "no blockers; 1 warning(s)" in capsys.readouterr().out


def test_edge_branches_are_covered(tmp_path):
    """No config file at all; a line-length that fits the header; no workflows dir."""
    # no .vibey-gh.toml -> unknown-key check has nothing to read
    (tmp_path / "pyproject.toml").write_text(
        '[tool.ruff]\nline-length = 400\n[tool.ruff.lint]\nselect = ["E"]\n'
    )
    findings = doctor.diagnose(cfg=GhConfig(root=tmp_path))
    # header fits inside 400 chars -> no E501 finding; no workflows dir -> no contention
    assert findings == [] or all("E501" not in f.message for f in findings)
