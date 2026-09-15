# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Repository-profile configuration stays portable and refuses invalid metadata."""

from pathlib import Path

import pytest

from vibey_gh import install
from vibey_gh.config import GhConfig, RepositoryProfileConfig, RulesetsConfig, load_config


def test_repository_profile_loads_from_toml(tmp_path: Path):
    (tmp_path / ".vibey-gh.toml").write_text(
        '[repository_profile]\nenabled=false\ndescription="A useful project"\n'
        'topics=["python", "automation"]\n'
    )
    assert load_config(tmp_path).repository_profile == RepositoryProfileConfig(
        enabled=False,
        description="A useful project",
        topics=("python", "automation"),
    )


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"description": "x" * 351}, "at most 350"),
        ({"topics": ("",)}, "non-empty"),
        ({"topics": ("same", "same")}, "unique"),
        ({"topics": tuple(f"topic-{index}" for index in range(21))}, "at most 20"),
        ({"topics": ("Has Space",)}, "lowercase"),
    ],
)
def test_repository_profile_rejects_invalid_metadata(kwargs, message):
    with pytest.raises(ValueError, match=message):
        RepositoryProfileConfig(**kwargs)


def test_repository_profile_workflow_renders_disabled_and_json_safe(tmp_path: Path):
    cfg = GhConfig(
        root=tmp_path,
        repository_profile=RepositoryProfileConfig(
            enabled=False,
            description='Quotes "stay" safe',
            topics=("python", "github-actions"),
        ),
    )
    rendered = install.render_workflow(install.WORKFLOWS / "repository-profile.yml", cfg)
    assert "false &&" in rendered
    assert 'CONFIG_DESCRIPTION: "Quotes \\"stay\\" safe"' in rendered
    assert '\'\u007b"names":\u005b"python","github-actions"\u005d\u007d\'' in rendered
    assert '"delete_branch_on_merge":false' in rendered
    assert '"vulnerability_alerts":true' in rendered


def test_repository_profile_workflow_renders_rulesets_disabled(tmp_path: Path):
    cfg = GhConfig(root=tmp_path, rulesets=RulesetsConfig(enabled=False))
    rendered = install.render_workflow(install.WORKFLOWS / "repository-profile.yml", cfg)
    assert "if: false" in rendered
    assert "if: true" not in rendered


def test_repository_profile_workflow_renders_rulesets_enabled_by_default(tmp_path: Path):
    cfg = GhConfig(root=tmp_path)
    rendered = install.render_workflow(install.WORKFLOWS / "repository-profile.yml", cfg)
    assert "if: true" in rendered
    assert "vibey-gh rulesets" in rendered
