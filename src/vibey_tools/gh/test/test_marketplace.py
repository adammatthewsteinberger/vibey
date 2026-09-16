# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""One marketplace at the root, rendered from the members: determinism, containment, loud drift."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any, ClassVar

import pytest

from vibey_gh import doctor
from vibey_gh.cli import _marketplace, main
from vibey_gh.config import GhConfig, MarketplaceConfig, load_config
from vibey_gh.marketplace import MANIFEST_PATH, MarketplaceError, MarketplaceRenderer

OWNER = {"name": "Owner", "email": "o@example.com"}
MEMBERS = ("src/tools/skills", "src/tools/gh")


def _plugin(name: str, source: str | None = None, **extra: Any) -> dict[str, Any]:
    return {
        "name": name,
        "source": source or f"./plugins/{name}",
        "description": f"{name} desc",
        **extra,
    }


def _member(
    root: Path,
    path: str,
    name: str,
    plugins: list[Any],
    *,
    owner: Any = OWNER,
    version: str | int | None = "1.2.3",
) -> Path:
    base = root / path
    (base / ".claude-plugin").mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {"name": name, "owner": owner, "plugins": plugins}
    if version is not None:
        manifest["metadata"] = {"version": version}
    (base / MANIFEST_PATH).write_text(json.dumps(manifest), encoding="utf-8")
    for plugin in plugins:
        source = plugin.get("source") if isinstance(plugin, dict) else None
        if isinstance(source, str) and source.startswith("./") and ".." not in source:
            plugin_dir = base / source[2:]
            (plugin_dir / ".claude-plugin").mkdir(parents=True, exist_ok=True)
            (plugin_dir / ".claude-plugin/plugin.json").write_text(
                json.dumps({"name": plugin["name"]}), encoding="utf-8"
            )
    return base


def _workspace(root: Path, **config: Any) -> GhConfig:
    _member(root, MEMBERS[0], "skills", [_plugin("alpha", version="0.1.0"), _plugin("beta")])
    _member(
        root,
        MEMBERS[1],
        "gh",
        [_plugin("gh-dev", category="development")],
        version=9,
    )
    return GhConfig(
        root=root, marketplace=MarketplaceConfig(name="vibey", members=MEMBERS, **config)
    )


@pytest.fixture
def workspace(tmp_path: Path) -> GhConfig:
    return _workspace(tmp_path)


# --- build ---------------------------------------------------------------------------


def test_build_re_roots_every_source_and_keeps_every_other_field(workspace: GhConfig):
    manifest = MarketplaceRenderer().build(workspace)
    assert manifest["name"] == "vibey"
    assert manifest["$schema"].startswith("https://json.schemastore.org/")
    assert manifest["owner"] == OWNER  # the first member's
    sources = [p["source"] for p in manifest["plugins"]]
    assert sources == [
        "./src/tools/skills/plugins/alpha",
        "./src/tools/skills/plugins/beta",
        "./src/tools/gh/plugins/gh-dev",
    ]
    alpha, _, gh_dev = manifest["plugins"]
    assert alpha["version"] == "0.1.0" and alpha["description"] == "alpha desc"
    assert gh_dev["category"] == "development"
    assert manifest["metadata"]["members"] == [
        {"path": "src/tools/skills", "name": "skills", "version": "1.2.3"},
        {"path": "src/tools/gh", "name": "gh", "version": "9"},
    ]
    description = manifest["metadata"]["description"]
    assert "3 plugin(s)" in description and "src/tools/skills, src/tools/gh" in description


def test_a_configured_description_replaces_the_derived_one(tmp_path: Path):
    cfg = _workspace(tmp_path, description="Hand-written.")
    assert MarketplaceRenderer().build(cfg)["metadata"]["description"] == "Hand-written."


def test_a_member_without_metadata_records_an_empty_version(tmp_path: Path):
    _member(tmp_path, "m", "m", [_plugin("one")], version=None)
    cfg = GhConfig(root=tmp_path, marketplace=MarketplaceConfig(name="x", members=("m",)))
    assert MarketplaceRenderer().build(cfg)["metadata"]["members"][0]["version"] == ""


def test_a_top_level_version_is_recorded_when_metadata_has_none(tmp_path: Path):
    """vibey-gh's own manifest predates the schema's `metadata.version` placement."""
    _member(tmp_path, "m", "m", [_plugin("one")], version=None)
    path = tmp_path / "m" / MANIFEST_PATH
    path.write_text(json.dumps({**json.loads(path.read_text()), "version": "1.0.0"}), "utf-8")
    cfg = GhConfig(root=tmp_path, marketplace=MarketplaceConfig(name="x", members=("m",)))
    assert MarketplaceRenderer().build(cfg)["metadata"]["members"][0]["version"] == "1.0.0"


def test_a_remote_source_passes_through_untouched(tmp_path: Path):
    remote = {"name": "far", "source": {"source": "github", "repo": "o/r"}}
    _member(tmp_path, "m", "m", [remote])
    cfg = GhConfig(root=tmp_path, marketplace=MarketplaceConfig(name="x", members=("m",)))
    assert MarketplaceRenderer().build(cfg)["plugins"] == [remote]


def test_build_refuses_when_no_members_are_declared(tmp_path: Path):
    with pytest.raises(MarketplaceError, match="members is empty"):
        MarketplaceRenderer().build(GhConfig(root=tmp_path))


@pytest.mark.parametrize(
    ("manifest", "message"),
    [
        ("{", "is invalid JSON"),
        ("[]", "has no name"),
        ('{"owner": {"name": "o"}, "plugins": [{"name": "a", "source": "./a"}]}', "has no name"),
        ('{"name": "m", "plugins": [{"name": "a", "source": "./a"}]}', "declares no owner"),
        (
            '{"name": "m", "owner": {}, "plugins": [{"name": "a", "source": "./a"}]}',
            "declares no owner",
        ),
        ('{"name": "m", "owner": {"name": "o"}}', "has no plugins"),
        ('{"name": "m", "owner": {"name": "o"}, "plugins": []}', "has no plugins"),
        ('{"name": "m", "owner": {"name": "o"}, "plugins": [1]}', "a plugin entry has no name"),
        ('{"name": "m", "owner": {"name": "o"}, "plugins": [{"source": "./a"}]}', "has no name"),
        ('{"name": "m", "owner": {"name": "o"}, "plugins": [{"name": "a"}]}', "'a' has no source"),
        (
            '{"name": "m", "owner": {"name": "o"}, "plugins": [{"name": "a", "source": "plugins/a"}]}',
            "must be a ./-relative path",
        ),
        (
            '{"name": "m", "owner": {"name": "o"}, "plugins": [{"name": "a", "source": "./plugins\\\\a"}]}',
            "must be a ./-relative path",
        ),
        (
            '{"name": "m", "owner": {"name": "o"}, "plugins": [{"name": "a", "source": "./../a"}]}',
            "must be a ./-relative path",
        ),
        (
            '{"name": "m", "owner": {"name": "o"}, "plugins": [{"name": "a", "source": "./nowhere"}]}',
            "has no .claude-plugin/plugin.json at ./m/nowhere",
        ),
    ],
)
def test_build_names_the_member_defect(tmp_path: Path, manifest: str, message: str):
    (tmp_path / "m/.claude-plugin").mkdir(parents=True)
    (tmp_path / "m" / MANIFEST_PATH).write_text(manifest, encoding="utf-8")
    cfg = GhConfig(root=tmp_path, marketplace=MarketplaceConfig(name="x", members=("m",)))
    with pytest.raises(MarketplaceError, match=message):
        MarketplaceRenderer().build(cfg)


def test_build_refuses_a_member_without_a_manifest(tmp_path: Path):
    cfg = GhConfig(root=tmp_path, marketplace=MarketplaceConfig(name="x", members=("m",)))
    with pytest.raises(MarketplaceError, match=f"m/{MANIFEST_PATH} is missing"):
        MarketplaceRenderer().build(cfg)


def test_build_refuses_one_plugin_name_from_two_members(tmp_path: Path):
    _member(tmp_path, "a", "a", [_plugin("same")])
    _member(tmp_path, "b", "b", [_plugin("same")])
    cfg = GhConfig(root=tmp_path, marketplace=MarketplaceConfig(name="x", members=("a", "b")))
    with pytest.raises(MarketplaceError, match="'same' is declared by both a and b"):
        MarketplaceRenderer().build(cfg)


# --- write / check -------------------------------------------------------------------


def test_write_is_deterministic_and_check_passes_on_its_own_output(workspace: GhConfig):
    renderer = MarketplaceRenderer()
    first = renderer.write(workspace).read_bytes()
    second = renderer.write(workspace).read_bytes()
    assert first == second and first.endswith(b"}\n")
    assert (workspace.root / MANIFEST_PATH).read_bytes() == first
    ok, message = renderer.check(workspace)
    assert ok and "2 member(s): 3 plugin(s) as 'vibey'" in message


def test_check_reports_a_missing_root_manifest(workspace: GhConfig):
    ok, message = MarketplaceRenderer().check(workspace)
    assert not ok and message == f"{MANIFEST_PATH} is missing — run `vibey-gh marketplace`"


def test_check_reports_drift_from_the_members(workspace: GhConfig):
    renderer = MarketplaceRenderer()
    target = renderer.write(workspace)
    target.write_text(target.read_text(encoding="utf-8").replace("alpha", "omega"), "utf-8")
    ok, message = renderer.check(workspace)
    assert not ok and "out of date with its members" in message


def test_check_reports_a_member_defect_as_a_failed_check(workspace: GhConfig):
    MarketplaceRenderer().write(workspace)
    (workspace.root / MEMBERS[1] / MANIFEST_PATH).unlink()
    ok, message = MarketplaceRenderer().check(workspace)
    assert not ok and message == f"{MEMBERS[1]}/{MANIFEST_PATH} is missing"


# --- configuration -------------------------------------------------------------------


def test_the_default_declares_no_marketplace():
    assert MarketplaceConfig() == MarketplaceConfig(name="", members=(), description="")


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"name": "vibey"}, "name is set but marketplace.members is empty"),
        ({"members": ("a",)}, "must be kebab-case"),
        ({"name": "Vibey", "members": ("a",)}, "must be kebab-case"),
        ({"name": "vibey_x", "members": ("a",)}, "must be kebab-case"),
        ({"name": "x", "members": ("/abs",)}, "repository-relative"),
        ({"name": "x", "members": ("~/home",)}, "repository-relative"),
        ({"name": "x", "members": ("a/../b",)}, "repository-relative"),
        ({"name": "x", "members": ("a b",)}, "repository-relative"),
        ({"name": "x", "members": ("a", "a")}, "must be unique"),
        ({"name": "x", "members": ("",)}, "must be non-empty"),
    ],
)
def test_the_configuration_refuses_what_claude_code_would_choke_on(kwargs: dict, message: str):
    with pytest.raises(ValueError, match=message):
        MarketplaceConfig(**kwargs)


# --- the command ---------------------------------------------------------------------


@pytest.fixture
def repo(tmp_path: Path, monkeypatch) -> Path:
    def git(*a: str) -> None:
        subprocess.run(["git", *a], cwd=tmp_path, capture_output=True, check=True)

    git("init", "-q", ".")
    git("config", "user.email", "t@example.com")
    git("config", "user.name", "t")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "__init__.py").write_text('__version__ = "1.0.0"\n')
    _workspace(tmp_path)
    (tmp_path / ".vibey-gh.toml").write_text(
        '[fingerprint]\nsources = ["src/*.py"]\n'
        '[version]\nfiles = ["src/__init__.py"]\ncode_paths = ["src/"]\n'
        '[merge_train]\nowner = "owner"\ntrusted_authors = ["owner"]\n'
        "[documentation]\nenabled = false\n"
        '[marketplace]\nname = "vibey"\nmembers = ["src/tools/skills", "src/tools/gh"]\n'
    )
    git("add", "-A")
    git("commit", "-qm", "base")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_doctor_knows_the_section_and_names_a_misspelt_key(repo: Path):
    assert not [f for f in doctor.diagnose(root=repo) if "marketplace" in f.message]
    config = repo / ".vibey-gh.toml"
    config.write_text(config.read_text() + 'descriptin = "typo"\n')
    findings = doctor.diagnose(root=repo)
    assert any("descriptin" in f.message and f.severity == "error" for f in findings)


def test_load_config_reads_the_marketplace_section(repo: Path):
    assert load_config().marketplace == MarketplaceConfig(name="vibey", members=MEMBERS)


def test_load_config_defaults_to_no_marketplace(repo: Path):
    config = repo / ".vibey-gh.toml"
    config.write_text(config.read_text().split("[marketplace]")[0])
    assert load_config().marketplace == MarketplaceConfig()


def test_the_command_writes_then_checks_clean(repo: Path, capsys):
    assert main(["marketplace"]) == 0
    assert (
        f"wrote {MANIFEST_PATH} — 3 plugin(s) from 2 member(s) as 'vibey'"
        in capsys.readouterr().out
    )
    assert main(["marketplace", "--check"]) == 0
    assert "matches its 2 member(s)" in capsys.readouterr().out


def test_the_command_fails_loudly_on_drift(repo: Path, capsys):
    main(["marketplace"])
    (repo / MANIFEST_PATH).write_text("{}\n", encoding="utf-8")
    assert main(["marketplace", "--check"]) == 1
    assert "out of date" in capsys.readouterr().err


def test_the_command_fails_loudly_without_members(repo: Path, capsys):
    config = repo / ".vibey-gh.toml"
    config.write_text(config.read_text().split("[marketplace]")[0])
    assert main(["marketplace"]) == 1
    assert "members is empty" in capsys.readouterr().err


def test_the_command_takes_any_renderer_at_its_seam(repo: Path, capsys):
    class Recorder:
        calls: ClassVar[list[str]] = []

        def build(self, cfg: GhConfig) -> dict[str, Any]:
            self.calls.append("build")
            return {"name": "fake", "plugins": []}

        def render(self, cfg: GhConfig) -> str:
            return "{}\n"

        def write(self, cfg: GhConfig) -> Path:
            self.calls.append("write")
            return cfg.root / MANIFEST_PATH

        def check(self, cfg: GhConfig) -> tuple[bool, str]:
            self.calls.append("check")
            return True, "fine"

    assert _marketplace(argparse.Namespace(check=True), renderer=Recorder()) == 0
    assert _marketplace(argparse.Namespace(check=False), renderer=Recorder()) == 0
    assert Recorder.calls == ["check", "build", "write"]
    out = capsys.readouterr().out
    assert "fine" in out and "0 plugin(s) from 2 member(s) as 'fake'" in out


def test_check_holds_the_root_manifest_to_its_members(repo: Path, capsys):
    main(["install"])
    assert main(["check", "--ci", "--apply"]) == 1  # declared members, nothing rendered yet
    assert f"marketplace: {MANIFEST_PATH} is missing" in capsys.readouterr().err
    assert main(["check", "--ci", "--quiet"]) == 1
    assert main(["marketplace"]) == 0
    assert main(["check", "--ci"]) == 0
    assert main(["check", "--ci", "--quiet"]) == 0
