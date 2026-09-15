# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""A0b/A0c harness path selection, copy-patch, monkeypatch restore, backups."""

from __future__ import annotations

import types
from pathlib import Path

import pytest

from agyloop.domain.classify import WITHDRAWN_INPUT_DETECTION_MODEL
from agyloop.infrastructure.agent.harness_retarget import (
    BACKUP_SUFFIX,
    HARNESS_PATH_ENV,
    INPUT_DETECTION_BINARY_ID,
    SKIP_SMOKE_ENV,
    apply_binary_path_monkeypatch,
    binary_contains_withdrawn,
    overwrite_site_packages_harness,
    patch_harness_bytes,
    prepare_harness,
    restore_harness,
    restore_site_packages_backup,
    restore_site_packages_backups,
    select_harness_path,
    smoke_check_harness,
    write_patched_copy,
)

_STOCK = b"hdr\0" + WITHDRAWN_INPUT_DETECTION_MODEL.encode("ascii") + b"\0tail"


def test_patch_harness_bytes_same_length_live_id() -> None:
    patched = patch_harness_bytes(_STOCK)
    assert WITHDRAWN_INPUT_DETECTION_MODEL.encode("ascii") not in patched
    assert INPUT_DETECTION_BINARY_ID.encode("ascii") in patched
    assert len(patched) == len(_STOCK)


def test_select_harness_path_honors_operator(tmp_path: Path) -> None:
    patched = tmp_path / "patched"
    patched.write_bytes(b"x")
    assert select_harness_path(operator_path="/opt/custom", patched=patched) == "/opt/custom"
    assert select_harness_path(operator_path=None, patched=patched) == str(patched)
    assert select_harness_path(operator_path=None, patched=None) is None


def test_prepare_harness_does_not_override_preset_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AGYLOOP_SKIP_HARNESS_RETARGET", "0")
    monkeypatch.setenv(HARNESS_PATH_ENV, "/already/set")
    monkeypatch.setenv("AGYLOOP_HARNESS_CACHE", str(tmp_path / "cache"))
    session = prepare_harness(enable_proxy_if_needed=False)
    try:
        assert os_env_harness() == "/already/set"
        assert "operator_harness_path" in session.notes
    finally:
        restore_harness()
        monkeypatch.setenv(HARNESS_PATH_ENV, "/already/set")


def os_env_harness() -> str | None:
    import os

    return os.environ.get(HARNESS_PATH_ENV)


def test_prepare_harness_copy_patch_sets_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import os

    stock = tmp_path / "localharness"
    stock.write_bytes(_STOCK)
    stock.chmod(0o755)
    cache = tmp_path / "cache"
    monkeypatch.setenv("AGYLOOP_SKIP_HARNESS_RETARGET", "0")
    monkeypatch.delenv(HARNESS_PATH_ENV, raising=False)
    monkeypatch.setenv("AGYLOOP_HARNESS_CACHE", str(cache))
    monkeypatch.setenv("AGYLOOP_NO_SITE_PACKAGES_PATCH", "1")
    # _STOCK is opaque bytes, not a real executable. This test covers path
    # selection and patching; runnability is covered by the smoke-check tests.
    monkeypatch.setenv(SKIP_SMOKE_ENV, "1")
    monkeypatch.setattr(
        "agyloop.infrastructure.agent.harness_retarget.stock_harness_path",
        lambda: stock,
    )
    session = prepare_harness(enable_proxy_if_needed=False)
    try:
        assert session.patched_binary is not None
        assert os.environ[HARNESS_PATH_ENV] == str(session.patched_binary)
        assert not binary_contains_withdrawn(session.patched_binary)
        assert "copy_patch" in session.notes
    finally:
        restore_harness()


def test_write_patched_copy_roundtrip(tmp_path: Path) -> None:
    stock = tmp_path / "localharness"
    stock.write_bytes(_STOCK)
    dest = tmp_path / "out" / "localharness"
    write_patched_copy(stock, dest)
    assert dest.is_file()
    assert not binary_contains_withdrawn(dest)


def test_monkeypatch_restores_stub_module(tmp_path: Path) -> None:
    stub = types.SimpleNamespace(_get_default_binary_path_external=lambda: "/stock")
    patched = tmp_path / "patched"
    patched.write_bytes(b"ok")
    restore = apply_binary_path_monkeypatch(stub, patched_binary=patched)
    assert stub._get_default_binary_path_external() == str(patched)
    restore()
    assert stub._get_default_binary_path_external() == "/stock"


def test_site_packages_backup_and_restore(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AGYLOOP_NO_SITE_PACKAGES_PATCH", raising=False)
    stock = tmp_path / "localharness"
    stock.write_bytes(_STOCK)
    backup = overwrite_site_packages_harness(stock)
    assert backup is not None
    assert backup.name.endswith(BACKUP_SUFFIX)
    assert backup.read_bytes() == _STOCK
    assert not binary_contains_withdrawn(stock)
    restore_site_packages_backup(backup)
    assert stock.read_bytes() == _STOCK
    assert not backup.is_file()


def test_site_packages_overwrite_preserves_executable_bit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The stock binary ships executable; overwriting it in place must not
    silently strip that bit. A stock file created only via write_bytes (as
    in test_site_packages_backup_and_restore above) is never executable in
    the first place, so that test can't catch a regression here -- this one
    starts from an explicitly-chmod'd stock file, matching the real wheel."""
    monkeypatch.delenv("AGYLOOP_NO_SITE_PACKAGES_PATCH", raising=False)
    stock = tmp_path / "localharness"
    stock.write_bytes(_STOCK)
    stock.chmod(0o755)

    backup = overwrite_site_packages_harness(stock)

    assert backup is not None
    assert stock.stat().st_mode & 0o777 == 0o755
    assert backup.stat().st_mode & 0o777 == 0o755


def test_repair_harness_restores_backup(tmp_path: Path) -> None:
    stock = tmp_path / "localharness"
    stock.write_bytes(INPUT_DETECTION_BINARY_ID.encode("ascii"))
    backup = tmp_path / f"localharness{BACKUP_SUFFIX}"
    backup.write_bytes(_STOCK)
    message = restore_site_packages_backups(stock)
    assert "restored" in message
    assert stock.read_bytes() == _STOCK


def _executable(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)
    return path


def test_smoke_check_passes_for_a_binary_that_starts(tmp_path: Path) -> None:
    harness = _executable(tmp_path / "localharness", "#!/bin/sh\nexec cat >/dev/null\n")
    assert smoke_check_harness(harness, timeout=2.0) is None


def test_smoke_check_passes_for_a_binary_that_blocks(tmp_path: Path) -> None:
    """Staying alive is the success signal -- the real harness waits on stdio."""
    harness = _executable(tmp_path / "localharness", "#!/bin/sh\nsleep 30\n")
    assert smoke_check_harness(harness, timeout=0.5) is None


def test_smoke_check_rejects_a_binary_that_dies_immediately(tmp_path: Path) -> None:
    """Reproduces a copy missing a sibling resource: it exits before writing its
    length header, which surfaces as 'Failed to read length from stdout'."""
    harness = _executable(
        tmp_path / "localharness",
        "#!/bin/sh\necho 'language_server_macos_arm64: no such file' >&2\nexit 1\n",
    )
    reason = smoke_check_harness(harness, timeout=2.0)
    assert reason is not None
    assert "exit_1" in reason
    assert "language_server_macos_arm64" in reason


def test_smoke_check_is_verified_once_per_copy(tmp_path: Path) -> None:
    harness = _executable(tmp_path / "localharness", "#!/bin/sh\nexit 0\n")
    assert smoke_check_harness(harness, timeout=2.0) is None
    marker = harness.with_name("localharness.verified")
    assert marker.is_file()
    # Break the binary but leave the marker: a matching stamp short-circuits.
    assert smoke_check_harness(harness, timeout=2.0) is None


def test_smoke_check_honours_the_operator_opt_out(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    harness = _executable(tmp_path / "localharness", "#!/bin/sh\nexit 3\n")
    monkeypatch.setenv(SKIP_SMOKE_ENV, "1")
    assert smoke_check_harness(harness, timeout=2.0) is None


def test_copy_patch_mirrors_sibling_resources(tmp_path: Path) -> None:
    """The harness resolves resources next to its own binary; copying only the
    binary into an empty cache dir is what leaves them missing."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    stock = bin_dir / "localharness"
    stock.write_bytes(_STOCK)
    (bin_dir / "language_server_macos_arm64").write_bytes(b"sibling")
    dest = tmp_path / "cache" / "localharness"

    write_patched_copy(stock, dest)

    assert (dest.parent / "language_server_macos_arm64").read_bytes() == b"sibling"
