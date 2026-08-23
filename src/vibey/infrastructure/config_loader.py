# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
import os
from pathlib import Path

from vibey.domain.config import VibeyConfig, parse_config, parse_toml_string


def load_config_from_path(path: Path) -> VibeyConfig:
    data = parse_toml_string(path.read_text())
    override = os.environ.get("VIBEY_FEATURE_QWENLOOP")
    if override is not None:
        normalized = override.strip().lower()
        if normalized not in {"0", "1", "false", "true", "no", "yes", "off", "on"}:
            raise ValueError("VIBEY_FEATURE_QWENLOOP must be a boolean value")
        features = data.setdefault("features", {})
        if not isinstance(features, dict):
            raise ValueError("features must be a table")
        features["qwenloop"] = normalized in {"1", "true", "yes", "on"}
    return parse_config(data)
