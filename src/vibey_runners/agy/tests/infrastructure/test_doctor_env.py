# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""DoctorEnvironment resolves GOOGLE_API_KEY vs ADC without guessing the lane."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from agyloop.infrastructure.doctor_env import RealDoctorEnvironment


def _env(
    monkeypatch: pytest.MonkeyPatch,
    *,
    home: Path,
    values: dict[str, str | None],
) -> RealDoctorEnvironment:
    for key in (
        "GOOGLE_API_KEY",
        "GEMINI_API_KEY",
        "GOOGLE_APPLICATION_CREDENTIALS",
        "GOOGLE_GENAI_USE_VERTEXAI",
        "GOOGLE_GENAI_USE_ENTERPRISE",
        "GOOGLE_CLOUD_PROJECT",
        "GOOGLE_CLOUD_LOCATION",
        "CLOUDSDK_CONFIG",
    ):
        monkeypatch.delenv(key, raising=False)
    for key, value in values.items():
        if value is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, value)
    return RealDoctorEnvironment(environ=os.environ, home=home)


def test_google_api_key_selects_developer_api_lane(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    env = _env(monkeypatch, home=tmp_path, values={"GOOGLE_API_KEY": "test-key"})
    auth = env.resolve_auth()
    assert auth.authenticated is True
    assert auth.lane == "developer_api"
    assert auth.source == "GOOGLE_API_KEY"


def test_adc_credentials_file_is_reported_without_guessing_lane(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    adc = tmp_path / "adc.json"
    adc.write_text("{}", encoding="utf-8")
    env = _env(
        monkeypatch,
        home=tmp_path,
        values={"GOOGLE_APPLICATION_CREDENTIALS": str(adc)},
    )
    auth = env.resolve_auth()
    assert auth.authenticated is True
    assert auth.lane == "unresolved"
    assert auth.source == "GOOGLE_APPLICATION_CREDENTIALS"


def test_well_known_adc_is_reported_as_adc_source(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    well_known = tmp_path / ".config" / "gcloud" / "application_default_credentials.json"
    well_known.parent.mkdir(parents=True)
    well_known.write_text("{}", encoding="utf-8")
    env = _env(monkeypatch, home=tmp_path, values={})
    auth = env.resolve_auth()
    assert auth.authenticated is True
    assert auth.lane == "unresolved"
    assert auth.source == "ADC_WELL_KNOWN"


def test_vertex_env_plus_adc_selects_enterprise_lane(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    adc = tmp_path / "adc.json"
    adc.write_text("{}", encoding="utf-8")
    env = _env(
        monkeypatch,
        home=tmp_path,
        values={
            "GOOGLE_GENAI_USE_VERTEXAI": "true",
            "GOOGLE_APPLICATION_CREDENTIALS": str(adc),
            "GOOGLE_CLOUD_PROJECT": "proj",
        },
    )
    auth = env.resolve_auth()
    assert auth.authenticated is True
    assert auth.lane == "enterprise"
    assert "GOOGLE_GENAI_USE_VERTEXAI" in auth.source


def test_gemini_api_key_selects_developer_api_lane(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    env = _env(monkeypatch, home=tmp_path, values={"GEMINI_API_KEY": "gemini-key"})
    auth = env.resolve_auth()
    assert auth.authenticated is True
    assert auth.lane == "developer_api"
    assert auth.source == "GEMINI_API_KEY"


def test_google_api_key_wins_over_gemini_api_key(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    env = _env(
        monkeypatch,
        home=tmp_path,
        values={"GOOGLE_API_KEY": "google-key", "GEMINI_API_KEY": "gemini-key"},
    )
    auth = env.resolve_auth()
    assert auth.source == "GOOGLE_API_KEY"


def test_neither_api_key_nor_adc_is_unauthenticated(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    env = _env(monkeypatch, home=tmp_path, values={})
    auth = env.resolve_auth()
    assert auth.authenticated is False
    assert auth.lane == "unresolved"
    assert auth.source == "none"


def test_conflicting_api_key_and_vertex_does_not_guess_lane(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    env = _env(
        monkeypatch,
        home=tmp_path,
        values={"GOOGLE_API_KEY": "key", "GOOGLE_GENAI_USE_VERTEXAI": "true"},
    )
    auth = env.resolve_auth()
    assert auth.lane == "unresolved"
    assert auth.authenticated is False
    assert "conflict" in auth.source or "conflict" in auth.detail.lower()


def test_doctor_asserts_no_interactive_hooks() -> None:
    env = RealDoctorEnvironment()
    assert env.interactive_hooks_registered() is False


def test_enterprise_flag_without_and_with_adc(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # 1. Enterprise without ADC
    env = _env(monkeypatch, home=tmp_path, values={"GOOGLE_GENAI_USE_ENTERPRISE": "1"})
    auth = env.resolve_auth()
    assert auth.authenticated is False
    assert auth.lane == "enterprise"
    assert "ADC was not found" in auth.detail

    # 2. Enterprise with ADC
    adc = tmp_path / "adc.json"
    adc.write_text("{}", encoding="utf-8")
    env2 = _env(
        monkeypatch,
        home=tmp_path,
        values={
            "GOOGLE_GENAI_USE_ENTERPRISE": "1",
            "GOOGLE_APPLICATION_CREDENTIALS": str(adc),
        },
    )
    auth2 = env2.resolve_auth()
    assert auth2.authenticated is True
    assert auth2.lane == "enterprise"
    assert "GOOGLE_GENAI_USE_ENTERPRISE" in auth2.source


def test_cloudsdk_config_well_known_adc(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    sdk_dir = tmp_path / "custom_cloudsdk"
    sdk_dir.mkdir(parents=True)
    adc_file = sdk_dir / "application_default_credentials.json"
    adc_file.write_text("{}", encoding="utf-8")

    env = _env(monkeypatch, home=tmp_path, values={"CLOUDSDK_CONFIG": str(sdk_dir)})
    auth = env.resolve_auth()
    assert auth.authenticated is True
    assert auth.source == "ADC_WELL_KNOWN"


def test_find_and_version_agy_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import subprocess
    from unittest.mock import patch

    env = RealDoctorEnvironment(home=tmp_path)
    assert env.configured_mcp_servers() == []

    # Successful version
    with patch("shutil.which", return_value="/usr/local/bin/agy"):
        assert env.find_agy_cli() == "/usr/local/bin/agy"

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=["agy", "--version"],
            returncode=0,
            stdout="agy 0.2.0\n",
        )
        assert env.agy_cli_version("/usr/local/bin/agy") == "agy 0.2.0"

        # Nonzero
        mock_run.return_value = subprocess.CompletedProcess(
            args=["agy", "--version"],
            returncode=1,
            stdout="",
        )
        assert env.agy_cli_version("/usr/local/bin/agy") is None

        # Timeout
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["agy"], timeout=10)
        assert env.agy_cli_version("/usr/local/bin/agy") is None


def test_doctor_interactive_hooks_registered_true() -> None:
    from unittest.mock import patch

    from google.antigravity.utils.interactive import ToolConfirmationHook

    env = RealDoctorEnvironment()
    with patch(
        "agyloop.infrastructure.doctor_env.autonomy_hooks", return_value=[ToolConfirmationHook()]
    ):
        assert env.interactive_hooks_registered() is True

    class CustomInteractiveHook:
        pass

    CustomInteractiveHook.__module__ = "google.antigravity.utils.interactive.sub"
    with patch(
        "agyloop.infrastructure.doctor_env.autonomy_hooks", return_value=[CustomInteractiveHook()]
    ):
        assert env.interactive_hooks_registered() is True


def test_check_sdk_harness_when_sdk_not_installed(tmp_path: Path) -> None:
    from unittest.mock import patch

    env = RealDoctorEnvironment(home=tmp_path)
    with patch("agyloop.infrastructure.doctor_env.stock_harness_path", return_value=None):
        status = env.check_sdk_harness()
        assert status.available is False
        assert "not installed" in status.detail.lower()


def test_check_sdk_harness_with_patched_harness_pass(tmp_path: Path) -> None:
    from unittest.mock import patch

    env = RealDoctorEnvironment(home=tmp_path)
    cache_path = tmp_path / ".cache" / "agyloop"
    patched_harness = cache_path / "localharness"
    patched_harness.parent.mkdir(parents=True, exist_ok=True)
    patched_harness.write_text("#!/bin/sh\necho test")

    with (
        patch("agyloop.infrastructure.doctor_env.stock_harness_path", return_value="/some/path"),
        patch("agyloop.infrastructure.doctor_env.cache_dir", return_value=cache_path),
        patch("agyloop.infrastructure.doctor_env.smoke_check_harness", return_value=None),
    ):
        status = env.check_sdk_harness()
        assert status.available is True
        assert "verified" in status.detail


def test_check_sdk_harness_with_patched_harness_fail(tmp_path: Path) -> None:
    from unittest.mock import patch

    env = RealDoctorEnvironment(home=tmp_path)
    cache_path = tmp_path / ".cache" / "agyloop"
    patched_harness = cache_path / "localharness"
    patched_harness.parent.mkdir(parents=True, exist_ok=True)
    patched_harness.write_text("#!/bin/sh\necho test")

    with (
        patch("agyloop.infrastructure.doctor_env.stock_harness_path", return_value="/some/path"),
        patch("agyloop.infrastructure.doctor_env.cache_dir", return_value=cache_path),
        patch("agyloop.infrastructure.doctor_env.smoke_check_harness", return_value="timeout"),
    ):
        status = env.check_sdk_harness()
        assert status.available is False
        assert "SDK harness issue" in status.detail
        assert "timeout" in status.detail


def test_check_sdk_harness_stock_no_patch(tmp_path: Path) -> None:
    from unittest.mock import patch

    env = RealDoctorEnvironment(home=tmp_path)
    cache_path = tmp_path / ".cache" / "agyloop"
    stock_path = Path("/usr/local/bin/localharness")

    with (
        patch("agyloop.infrastructure.doctor_env.stock_harness_path", return_value=stock_path),
        patch("agyloop.infrastructure.doctor_env.cache_dir", return_value=cache_path),
    ):
        status = env.check_sdk_harness()
        assert status.available is True
        assert "stock harness" in status.detail
        assert "no patch needed" in status.detail
