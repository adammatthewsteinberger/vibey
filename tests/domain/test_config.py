import pytest

from vibey.domain.config import ConfigError, load_config_from_string

ARCHITECTURE_DOC_EXAMPLE = """
[project]
name          = "my-app"
repo          = "."
max_cycles    = 10
strict_loopback = false          # true forces REVIEW -> DESIGN always

[isolation]
level         = "container"      # worktree | container | vm
allow_push    = false
egress        = [
    "api.anthropic.com", "api.openai.com", "api.cursor.sh", "generativelanguage.googleapis.com"
]

[budget]
max_dollars_per_cycle = 40.0
max_dollars_total     = 250.0
max_turns_per_item    = 60

[engines]
enabled = ["claudeloop", "codexloop", "cursorloop", "agyloop"]

[engines.weights]                # base rotation weights
claudeloop = 3
codexloop  = 2
cursorloop = 2
agyloop    = 1

[phases.design]
effort   = "high"
engines  = ["claudeloop", "codexloop"]     # optional per-phase allow-list

[phases.build]
effort      = "low"
parallelism = 4

[phases.review]
effort = "high"

[provision]
plugins = [
    "software-architecture", "quality-engineering", "security-first-dev", "engineering-process"
]

[deploy]
enabled = false
target  = "azure"
iac     = "bicep"
"""


def test_architecture_doc_example_parses_every_field() -> None:
    config = load_config_from_string(ARCHITECTURE_DOC_EXAMPLE)

    assert config.project.name == "my-app"
    assert config.project.repo == "."
    assert config.project.max_cycles == 10
    assert config.project.strict_loopback is False

    assert config.isolation.level == "container"
    assert config.isolation.allow_push is False
    assert config.isolation.egress == (
        "api.anthropic.com",
        "api.openai.com",
        "api.cursor.sh",
        "generativelanguage.googleapis.com",
    )

    assert config.budget.max_dollars_per_cycle == 40.0
    assert config.budget.max_dollars_total == 250.0
    assert config.budget.max_turns_per_item == 60

    assert config.engines.enabled == ("claudeloop", "codexloop", "cursorloop", "agyloop")
    assert config.engines.weights == {
        "claudeloop": 3,
        "codexloop": 2,
        "cursorloop": 2,
        "agyloop": 1,
    }

    assert config.phases.design.effort == "high"
    assert config.phases.design.engines == ("claudeloop", "codexloop")
    assert config.phases.build.effort == "low"
    assert config.phases.build.parallelism == 4
    assert config.phases.review.effort == "high"

    assert config.provision.plugins == (
        "software-architecture",
        "quality-engineering",
        "security-first-dev",
        "engineering-process",
    )

    assert config.deploy.enabled is False
    assert config.deploy.target == "azure"
    assert config.deploy.iac == "bicep"


def test_minimal_config_applies_defaults() -> None:
    config = load_config_from_string('[project]\nname = "tiny"\n')

    assert config.project.name == "tiny"
    assert config.project.max_cycles == 10
    assert config.isolation.level == "worktree"
    assert config.engines.enabled == (
        "claudeloop",
        "codexloop",
        "cursorloop",
        "agyloop",
    )
    assert config.phases.design.effort == "high"
    assert config.phases.build.effort == "low"
    assert config.phases.review.effort == "high"
    assert config.deploy.enabled is False


def test_missing_project_table_is_rejected() -> None:
    with pytest.raises(ConfigError):
        load_config_from_string("")


def test_missing_project_name_is_rejected() -> None:
    with pytest.raises(ConfigError):
        load_config_from_string('[project]\nrepo = "."\n')


def test_wrong_type_for_project_name_is_rejected() -> None:
    with pytest.raises(ConfigError):
        load_config_from_string("[project]\nname = 42\n")


def test_invalid_isolation_level_is_rejected() -> None:
    text = '[project]\nname = "x"\n\n[isolation]\nlevel = "chroot"\n'
    with pytest.raises(ConfigError):
        load_config_from_string(text)


def test_invalid_phase_effort_is_rejected() -> None:
    text = '[project]\nname = "x"\n\n[phases.build]\neffort = "extreme"\n'
    with pytest.raises(ConfigError):
        load_config_from_string(text)


def test_unknown_engine_in_enabled_list_is_rejected() -> None:
    text = '[project]\nname = "x"\n\n[engines]\nenabled = ["claudeloop", "chatgpt"]\n'
    with pytest.raises(ConfigError):
        load_config_from_string(text)


def test_unknown_engine_in_weights_is_rejected() -> None:
    text = '[project]\nname = "x"\n\n[engines.weights]\nchatgpt = 1\n'
    with pytest.raises(ConfigError):
        load_config_from_string(text)


def test_wrong_type_for_optional_field_is_rejected() -> None:
    text = '[project]\nname = "x"\n\n[isolation]\negress = "not-a-list"\n'
    with pytest.raises(ConfigError):
        load_config_from_string(text)


def test_require_reports_missing_field_by_path() -> None:
    from vibey.domain.config import _require

    with pytest.raises(ConfigError) as exc_info:
        _require({}, "name", "project.name", str)

    assert exc_info.value.path == "project.name"


def test_malformed_toml_raises() -> None:
    with pytest.raises(Exception):  # noqa: B017 - tomllib.TOMLDecodeError, not our concern
        load_config_from_string("[project\nname = 'x'")
