# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agyloop.domain.classify import WITHDRAWN_INPUT_DETECTION_MODEL
from agyloop.domain.model_profile import INPUT_DETECTION_MODEL
from agyloop.infrastructure.agent.harness_retarget import (
    _LOCAL_CONNECTION,
    BACKUP_SUFFIX,
    HarnessSession,
    _apply_sdk_monkeypatches,
    _atexit_restore,
    _maybe_start_proxy,
    binary_contains_withdrawn,
    cache_dir,
    input_detection_models,
    overwrite_site_packages_harness,
    patch_harness_bytes,
    prepare_harness,
    restore_harness,
    restore_site_packages_backup,
    restore_site_packages_backups,
    stock_harness_path,
)


def test_input_detection_models_pairs_the_chat_model_with_flash_lite() -> None:
    """The operator's chat model must survive: this list is passed as
    ``models=``, and returning only the input-detection target would suppress
    the model the run was actually started with."""
    targets = input_detection_models(chat_model="gemini-2.5-flash", api_key="k")
    assert [t.name for t in targets] == ["gemini-2.5-flash", INPUT_DETECTION_MODEL]


def test_input_detection_models_does_not_duplicate_the_alias() -> None:
    targets = input_detection_models(chat_model=INPUT_DETECTION_MODEL, api_key="k")
    assert [t.name for t in targets] == [INPUT_DETECTION_MODEL]


def test_input_detection_models_without_a_chat_model_yields_only_the_alias() -> None:
    targets = input_detection_models(chat_model=None, api_key="k")
    assert [t.name for t in targets] == [INPUT_DETECTION_MODEL]


def test_cache_dir_variants(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("AGYLOOP_HARNESS_CACHE", raising=False)
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "xdg"))
    assert cache_dir() == tmp_path / "xdg" / "agyloop" / "localharness"

    monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
    assert "localharness" in str(cache_dir())


def test_stock_harness_path_variants(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # Key error or OSError
    with patch.dict(sys.modules, {"google.antigravity.types": types.ModuleType("types")}):
        sys.modules["google.antigravity.types"].__file__ = None
        assert stock_harness_path() is None

    # Found binary
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(parents=True)
    harness = bin_dir / "localharness"
    harness.write_bytes(b"bin")
    mod = types.ModuleType("google.antigravity.types")
    mod.__file__ = str(tmp_path / "types.py")
    with patch.dict(sys.modules, {"google.antigravity.types": mod}):
        assert stock_harness_path() == harness

    # Found .exe
    harness.unlink()
    harness_exe = bin_dir / "localharness.exe"
    harness_exe.write_bytes(b"exe")
    with patch.dict(sys.modules, {"google.antigravity.types": mod}):
        assert stock_harness_path() == harness_exe


def test_binary_contains_withdrawn_error(tmp_path: Path) -> None:
    missing = tmp_path / "nonexistent"
    assert binary_contains_withdrawn(missing) is False


def test_patch_harness_bytes_unchanged() -> None:
    data = b"no withdrawn id here"
    assert patch_harness_bytes(data) == data


def test_apply_sdk_monkeypatches(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    session = HarnessSession()

    # Module cannot be imported
    with (
        patch("importlib.import_module", side_effect=ImportError),
        patch.dict(sys.modules, {_LOCAL_CONNECTION: None}, clear=False),
    ):
        sys.modules.pop(_LOCAL_CONNECTION, None)
        _apply_sdk_monkeypatches(session, patched_binary=None)
        assert session.monkeypatch_restore is None

    # Module exists with _get_default_binary_path_external and build_models_proto
    mod = types.ModuleType(_LOCAL_CONNECTION)
    mod._get_default_binary_path_external = lambda: "/orig/path"

    class FakeTarget:
        def __init__(self, name: str) -> None:
            self.name = name

        def model_copy(self, update: dict[str, str]) -> FakeTarget:
            return FakeTarget(update["name"])

    seen_models = []

    def fake_build_models(models: list[FakeTarget]) -> list[FakeTarget]:
        seen_models.extend(models)
        return models

    mod.build_models_proto = fake_build_models

    with patch.dict(sys.modules, {_LOCAL_CONNECTION: mod}):
        patched_file = tmp_path / "patched"
        patched_file.write_bytes(b"bin")
        _apply_sdk_monkeypatches(session, patched_binary=patched_file)
        assert mod._get_default_binary_path_external() == str(patched_file)

        # Call patched build_models_proto
        targets = [
            FakeTarget(f"models/{WITHDRAWN_INPUT_DETECTION_MODEL}"),
            FakeTarget("models/gemini-2.5-pro"),
        ]
        mod.build_models_proto(targets)
        assert seen_models[0].name == f"models/{INPUT_DETECTION_MODEL}"

        # Restore
        assert session.monkeypatch_restore is not None
        session.monkeypatch_restore()
        assert mod._get_default_binary_path_external() == "/orig/path"


def test_overwrite_site_packages_failures(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGYLOOP_NO_SITE_PACKAGES_PATCH", "1")
    stock = tmp_path / "localharness"
    stock.write_bytes(b"stock")
    assert overwrite_site_packages_harness(stock) is None

    monkeypatch.delenv("AGYLOOP_NO_SITE_PACKAGES_PATCH", raising=False)
    # Patched == original
    assert overwrite_site_packages_harness(stock) is None


def test_restore_site_packages_helpers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # restore_site_packages_backup on invalid path
    restore_site_packages_backup(tmp_path / "not_backup.txt")

    # The default target is resolved from the installed SDK, so this branch has
    # to be forced. Asserting it via the real default would pass only on a
    # machine without google.antigravity installed -- and fail on CI, where the
    # dependency is present.
    monkeypatch.setattr(
        "agyloop.infrastructure.agent.harness_retarget.stock_harness_path",
        lambda: None,
    )
    assert "no bundled localharness found" in restore_site_packages_backups(None)

    stock = tmp_path / "localharness"
    stock.write_bytes(b"live")
    assert "no backup" in restore_site_packages_backups(stock)


def test_restore_site_packages_backups_restores_from_the_backup(tmp_path: Path) -> None:
    """The repair path itself -- `agyloop doctor --repair-harness` is the only
    way back to a stock harness after a retarget, so it has to actually copy."""
    stock = tmp_path / "localharness"
    stock.write_bytes(b"patched")
    backup = stock.with_name(stock.name + BACKUP_SUFFIX)
    backup.write_bytes(b"stock")

    assert "restored" in restore_site_packages_backups(stock)
    assert stock.read_bytes() == b"stock"


def test_maybe_start_proxy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGYLOOP_GEMINI_REWRITE_PROXY", "1")

    session = HarnessSession()
    _maybe_start_proxy(session, enable=False)
    assert "proxy_disabled" in session.notes

    # Proxy OSError
    session_err = HarnessSession()
    with patch(
        "agyloop.infrastructure.agent.harness_retarget.GeminiRewriteProxy.start",
        side_effect=OSError("bind fail"),
    ):
        _maybe_start_proxy(session_err, enable=True)
        assert any("proxy_error" in note for note in session_err.notes)

    # Proxy successful start
    session_ok = HarnessSession()
    with patch(
        "agyloop.infrastructure.agent.harness_retarget.GeminiRewriteProxy.start",
        return_value="http://127.0.0.1:9999",
    ):
        _maybe_start_proxy(session_ok, enable=True)
        assert "rewrite_proxy" in session_ok.notes


def test_atexit_and_restore() -> None:
    restore_harness()
    _atexit_restore()


def test_prepare_harness_branch_conditions(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGYLOOP_SKIP_HARNESS_RETARGET", "0")
    monkeypatch.delenv("AGYLOOP_HARNESS_PATH", raising=False)

    # 1. No stock binary
    with patch(
        "agyloop.infrastructure.agent.harness_retarget.stock_harness_path", return_value=None
    ):
        session = prepare_harness(enable_proxy_if_needed=False)
        assert "no_stock_binary" in session.notes
        restore_harness()

    # 2. Stock already live
    live_stock = tmp_path / "live_stock"
    live_stock.write_bytes(b"live without withdrawn")
    with patch(
        "agyloop.infrastructure.agent.harness_retarget.stock_harness_path", return_value=live_stock
    ):
        session = prepare_harness(enable_proxy_if_needed=False)
        assert "stock_already_live" in session.notes
        restore_harness()

    # 3. Copy patch unrunnable falls through
    withdrawn_stock = tmp_path / "withdrawn_stock"
    withdrawn_stock.write_bytes(WITHDRAWN_INPUT_DETECTION_MODEL.encode("ascii"))
    with (
        patch(
            "agyloop.infrastructure.agent.harness_retarget.stock_harness_path",
            return_value=withdrawn_stock,
        ),
        patch(
            "agyloop.infrastructure.agent.harness_retarget.smoke_check_harness", return_value="died"
        ),
        patch(
            "agyloop.infrastructure.agent.harness_retarget.cache_dir",
            return_value=tmp_path / "cache",
        ),
    ):
        session = prepare_harness(enable_proxy_if_needed=True)
        assert any("copy_patch_unrunnable" in n for n in session.notes)
        restore_harness()


def test_harness_retarget_additional_edge_cases(tmp_path: Path) -> None:
    from agyloop.infrastructure.agent.harness_retarget import (
        HarnessSession,
        _apply_sdk_monkeypatches,
        copy_harness_siblings,
        restore_site_packages_backup,
        smoke_check_harness,
        stock_harness_path,
    )

    # 1. stock_harness_path with .exe
    with patch("pathlib.Path.is_file", side_effect=[False, True]):
        exe_path = stock_harness_path()
        assert exe_path is not None

    # 2. copy_harness_siblings with non-existent parent
    assert copy_harness_siblings(tmp_path / "nonexistent" / "stock", tmp_path / "dest") == []

    # 3. smoke_check_harness stat error
    missing_file = tmp_path / "missing_bin"
    assert "stat_failed" in (smoke_check_harness(missing_file) or "")

    # 4. smoke_check_harness spawn error
    real_bin = tmp_path / "real_bin"
    real_bin.write_bytes(b"dummy")
    with patch("subprocess.Popen", side_effect=OSError("exec format error")):
        assert "spawn_failed" in (smoke_check_harness(real_bin) or "")

    # 5. restore_site_packages_backup invalid name
    restore_site_packages_backup(tmp_path / "not_a_backup.txt")

    # 6. _apply_sdk_monkeypatches models proto rewriting
    session = HarnessSession()
    mock_module = MagicMock()
    original_models_fn = MagicMock(side_effect=lambda models: models)
    mock_module.build_models_proto = original_models_fn
    mock_module._get_default_binary_path_external = MagicMock(return_value="/orig/path")

    with patch.dict(
        "sys.modules", {"google.antigravity.connections.local.local_connection": mock_module}
    ):
        _apply_sdk_monkeypatches(session, patched_binary=tmp_path / "patched")
        assert session.monkeypatch_restore is not None

        # Call the monkeypatched build_models_proto
        class ModelMock:
            def __init__(self, name: str) -> None:
                self.name = name

            def model_copy(self, update: dict[str, str]) -> ModelMock:
                return ModelMock(update["name"])

        input_models = [ModelMock(WITHDRAWN_INPUT_DETECTION_MODEL), ModelMock("gemini-2.5-flash")]
        res = mock_module.build_models_proto(input_models)
        assert res[0].name != WITHDRAWN_INPUT_DETECTION_MODEL

        session.close()
