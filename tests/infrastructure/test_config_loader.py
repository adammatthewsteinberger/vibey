# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
from pathlib import Path

import pytest

from vibey.infrastructure.config_loader import load_config_from_path


def test_load_config_from_path_reads_and_parses(tmp_path: Path) -> None:
    config_path = tmp_path / "vibey.toml"
    config_path.write_text('[project]\nname = "from-disk"\n')

    config = load_config_from_path(config_path)

    assert config.project.name == "from-disk"


def test_environment_enables_qwenloop(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    config_path = tmp_path / "vibey.toml"
    config_path.write_text('[project]\nname = "from-disk"\n')
    monkeypatch.setenv("VIBEY_FEATURE_QWENLOOP", "yes")
    assert load_config_from_path(config_path).features.qwenloop


def test_invalid_environment_override_is_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config_path = tmp_path / "vibey.toml"
    config_path.write_text('[project]\nname = "from-disk"\n')
    monkeypatch.setenv("VIBEY_FEATURE_QWENLOOP", "maybe")
    with pytest.raises(ValueError, match="boolean"):
        load_config_from_path(config_path)


def test_environment_rejects_non_table_features(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config_path = tmp_path / "vibey.toml"
    config_path.write_text('features = "bad"\n[project]\nname = "from-disk"\n')
    monkeypatch.setenv("VIBEY_FEATURE_QWENLOOP", "true")
    with pytest.raises(ValueError, match="table"):
        load_config_from_path(config_path)
