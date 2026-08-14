from pathlib import Path

from vibey.infrastructure.config_loader import load_config_from_path


def test_load_config_from_path_reads_and_parses(tmp_path: Path) -> None:
    config_path = tmp_path / "vibey.toml"
    config_path.write_text('[project]\nname = "from-disk"\n')

    config = load_config_from_path(config_path)

    assert config.project.name == "from-disk"
