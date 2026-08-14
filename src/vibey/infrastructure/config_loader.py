from pathlib import Path

from vibey.domain.config import VibeyConfig, load_config_from_string


def load_config_from_path(path: Path) -> VibeyConfig:
    return load_config_from_string(path.read_text())
