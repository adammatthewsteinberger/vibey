# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Retarget Antigravity input-detection off withdrawn ``gemini-2.5-flash-lite``.

SDK facts (installed ``google-antigravity`` localharness):

- ``strings`` hits: one ``gemini-2.5-flash-lite`` literal, Go log
  ``error during input detection model call``, enum
  ``MODEL_GOOGLE_GEMINI_2_5_FLASH_LITE``. No public ``INPUT_DETECTION``
  ``ModelType``. ``LocalAgentConfig.env`` is copied into harness ``Popen``.
- Binary resolution: ``ANTIGRAVITY_HARNESS_PATH``, then wheel
  ``google/antigravity/bin/localharness``, then ``importlib.resources``,
  then ``PATH``.
- ``gemini-2.5-flash-lite`` is 21 bytes; ``gemini-flash-lite-latest`` is 24.
  Same-length live id ``gemini-3.5-flash-lite`` is used for the copy-patch.

Layers, in order: A0 env + extra ``ModelTarget``; A0b copy-patch via
``ANTIGRAVITY_HARNESS_PATH``; A0c monkeypatch / site-packages backup /
localhost rewrite proxy. Operator-set ``ANTIGRAVITY_HARNESS_PATH`` is never
clobbered. ``AGYLOOP_SKIP_HARNESS_RETARGET=1`` skips A0b/A0c (tests).
"""

from __future__ import annotations

import atexit
import importlib
import logging
import os
import shutil
import signal
import subprocess  # nosec B404 - fixed argv smoke check, never shell=True
import sys
import time
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from google.antigravity.types import GeminiAPIEndpoint, ModelTarget, ModelType

from agyloop.domain.classify import WITHDRAWN_INPUT_DETECTION_MODEL
from agyloop.domain.model_profile import INPUT_DETECTION_MODEL
from agyloop.infrastructure.agent.gemini_rewrite import (
    GeminiRewriteProxy,
    rewrite_proxy_disabled,
    rewrite_withdrawn_model_text,
)

_LOG = logging.getLogger(__name__)

HARNESS_PATH_ENV = "ANTIGRAVITY_HARNESS_PATH"
SKIP_RETARGET_ENV = "AGYLOOP_SKIP_HARNESS_RETARGET"
NO_SITE_PACKAGES_ENV = "AGYLOOP_NO_SITE_PACKAGES_PATCH"
BACKUP_SUFFIX = ".agyloop-bak"

# Same 21-byte Go string as the withdrawn id. Live SKU behind flash-lite-latest.
INPUT_DETECTION_BINARY_ID = "gemini-3.5-flash-lite"

_WITHDRAWN_BYTES = WITHDRAWN_INPUT_DETECTION_MODEL.encode("ascii")
_BINARY_LIVE_BYTES = INPUT_DETECTION_BINARY_ID.encode("ascii")
if len(_WITHDRAWN_BYTES) != len(_BINARY_LIVE_BYTES):  # pragma: no cover
    raise RuntimeError("input-detection binary patch ids must be the same length")

_LOCAL_CONNECTION = "google.antigravity.connections.local.local_connection"


def input_detection_env() -> dict[str, str]:
    """Env forwarded into ``LocalAgentConfig.env`` / harness ``Popen``."""
    return {"AGYLOOP_INPUT_DETECTION_MODEL": INPUT_DETECTION_MODEL}


def input_detection_models(
    *,
    chat_model: str | None,
    api_key: str | None,
    base_url: str | None = None,
) -> list[ModelTarget]:
    """Operator chat model first, then the live flash-lite alias as TEXT.

    Does not replace the operator-selected main model. When ``chat_model`` is
    unset, returns only the input-detection target — callers must not pass
    that list as ``models=`` or the SDK default TEXT model is suppressed.
    """
    endpoint = GeminiAPIEndpoint(api_key=api_key, base_url=base_url)
    lite = ModelTarget(
        name=INPUT_DETECTION_MODEL,
        types=[ModelType.TEXT],
        endpoint=endpoint,
    )
    if not chat_model:
        return [lite]
    chat = ModelTarget(name=chat_model, types=[ModelType.TEXT], endpoint=endpoint)
    if chat_model == INPUT_DETECTION_MODEL:
        return [chat]
    return [chat, lite]


def cache_dir() -> Path:
    override = os.environ.get("AGYLOOP_HARNESS_CACHE")
    if override:
        return Path(override)
    xdg = os.environ.get("XDG_CACHE_HOME")
    root = Path(xdg) if xdg else Path.home() / ".cache"
    return root / "agyloop" / "localharness"


def stock_harness_path() -> Path | None:
    try:
        types_file = sys.modules["google.antigravity.types"].__file__
        package_root = Path(types_file or ".").resolve().parent
        path = package_root / "bin" / "localharness"
        if path.is_file():
            return path
        exe = path.with_suffix(".exe")
        if exe.is_file():
            return exe
    except (KeyError, OSError, AttributeError):
        return None
    return None


def binary_contains_withdrawn(path: Path) -> bool:
    try:
        return _WITHDRAWN_BYTES in path.read_bytes()
    except OSError:
        return False


def patch_harness_bytes(data: bytes) -> bytes:
    """Same-length replace of the withdrawn Go string constant."""
    if _WITHDRAWN_BYTES not in data:
        return data
    return data.replace(_WITHDRAWN_BYTES, _BINARY_LIVE_BYTES)


def copy_harness_siblings(stock: Path, dest_dir: Path) -> list[str]:
    """Mirror every other file in the stock ``bin/`` next to the patched copy.

    The harness resolves some resources relative to its own directory (the
    binary carries ``language_server*`` symbols). Copying only the 101 MB
    binary into an otherwise-empty cache dir leaves those siblings missing, and
    the harness then dies before writing its 4-byte length header -- surfacing
    as ``RuntimeError: Failed to read length from stdout``.
    """
    copied: list[str] = []
    try:
        entries = sorted(stock.parent.iterdir())
    except OSError:
        return copied
    for entry in entries:
        if entry.name == stock.name or not entry.is_file():
            continue
        target = dest_dir / entry.name
        try:
            if target.exists() and target.stat().st_size == entry.stat().st_size:
                continue
            shutil.copy2(entry, target)
            copied.append(entry.name)
        except OSError:  # pragma: no cover - best effort, never fatal
            continue
    return copied


def write_patched_copy(stock: Path, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    patched = patch_harness_bytes(stock.read_bytes())
    # Rewriting 101 MB on every probe is pure waste; the patch is deterministic,
    # so an existing correct copy is already the answer.
    if not dest.is_file() or dest.read_bytes() != patched:
        dest.write_bytes(patched)
    dest.chmod(stock.stat().st_mode)
    # Re-sign the binary after patching to fix the invalidated code signature.
    # macOS kills processes with modified signatures (SIGKILL), which surfaces as
    # "Failed to read length from stdout" when the harness dies before writing
    # its 4-byte header. Ad-hoc signing is sufficient for local execution.
    # codesign may not be available on non-macOS, or may fail for other reasons.
    # The patched binary may still work on platforms without code signature enforcement.
    with suppress(OSError, subprocess.CalledProcessError):
        subprocess.run(  # nosec B603 B607 - fixed argv, codesign is a system binary
            ["codesign", "-s", "-", "--force", "--preserve-metadata=entitlements", str(dest)],
            check=True,
            capture_output=True,
        )
    copy_harness_siblings(stock, dest.parent)
    return dest


SMOKE_TIMEOUT_SECONDS = 3.0
SKIP_SMOKE_ENV = "AGYLOOP_SKIP_HARNESS_SMOKE"


def _kill_process_tree(proc: subprocess.Popen[bytes]) -> None:
    """Kill the smoke-check process and anything it spawned, then reap without
    blocking. ``communicate()`` with no timeout would wait on pipes a surviving
    grandchild still holds."""
    killpg = getattr(os, "killpg", None)
    getpgid = getattr(os, "getpgid", None)
    if killpg is not None and getpgid is not None:
        with suppress(OSError, ProcessLookupError):
            killpg(getpgid(proc.pid), signal.SIGKILL)
    with suppress(OSError, ProcessLookupError):
        proc.kill()
    with suppress(subprocess.TimeoutExpired, OSError):
        proc.communicate(timeout=1.0)


def smoke_check_harness(dest: Path, *, timeout: float = SMOKE_TIMEOUT_SECONDS) -> str | None:
    """Confirm the patched copy actually starts. Returns a reason on failure.

    The harness speaks a length-prefixed stdio protocol, so *staying alive* is
    the success signal -- there is no ``--version`` to ask. A copy that is
    missing a sibling resource exits immediately instead, which is precisely
    the failure that surfaces as ``Failed to read length from stdout`` several
    layers up. Verified once per distinct copy, not once per probe.
    """
    if os.environ.get(SKIP_SMOKE_ENV) == "1":
        return None
    marker = dest.with_name(dest.name + ".verified")
    try:
        stamp = f"{dest.stat().st_size}:{int(dest.stat().st_mtime)}"
    except OSError as exc:
        return f"stat_failed:{type(exc).__name__}"
    if marker.is_file():
        try:
            if marker.read_text(encoding="utf-8").strip() == stamp:
                return None
        except OSError:  # pragma: no cover - re-verify rather than trust
            pass
    try:
        proc = subprocess.Popen(  # nosec B603 - fixed argv, never shell=True
            [str(dest)],
            stdin=subprocess.PIPE,  # PIPE, not DEVNULL: harness waits for input
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            # Own process group: the harness spawns a language-server child, and
            # killing only the parent leaves the child holding the pipes, which
            # would make the reap below block for as long as the child lives.
            start_new_session=True,
        )
    except OSError as exc:
        return f"spawn_failed:{type(exc).__name__}:{exc}"
    # Poll for the timeout duration without closing stdin. communicate() would close
    # stdin immediately, causing the harness to hit EOF and exit before the window ends.
    end_time = time.monotonic() + timeout
    while time.monotonic() < end_time:
        if proc.poll() is not None:
            # Process exited before the timeout
            break
        time.sleep(0.1)

    if proc.poll() is None:
        # Still running after the window: it started. That is the pass case.
        _kill_process_tree(proc)
        with suppress(OSError):
            marker.write_text(stamp + "\n", encoding="utf-8")
        return None

    # Process exited during the window. Collect stderr for diagnostics.
    try:
        _, stderr = proc.communicate(timeout=1.0)
    except subprocess.TimeoutExpired:
        # Zombie or hung; treat as unrunnable
        _kill_process_tree(proc)
        return "exit_hung:process_exited_but_communicate_timed_out"

    if proc.returncode == 0:
        with suppress(OSError):
            marker.write_text(stamp + "\n", encoding="utf-8")
        return None
    detail = (stderr or b"").decode("utf-8", "replace").strip().splitlines()
    return f"exit_{proc.returncode}:{detail[-1][:200] if detail else 'no stderr'}"


@dataclass
class HarnessSession:
    patched_binary: Path | None = None
    set_harness_path: bool = False
    previous_harness_path: str | None = None
    monkeypatch_restore: Callable[[], None] | None = None
    site_backup: Path | None = None
    proxy: GeminiRewriteProxy | None = None
    notes: list[str] = field(default_factory=list)

    def close(self) -> None:
        if self.monkeypatch_restore is not None:
            self.monkeypatch_restore()
            self.monkeypatch_restore = None
        if self.proxy is not None:
            self.proxy.stop()
            self.proxy = None
        if self.site_backup is not None:
            restore_site_packages_backup(self.site_backup)
            self.site_backup = None
        if self.set_harness_path:
            if self.previous_harness_path is None:
                os.environ.pop(HARNESS_PATH_ENV, None)
            else:
                os.environ[HARNESS_PATH_ENV] = self.previous_harness_path
            self.set_harness_path = False


_atexit_registered = False
_active: HarnessSession | None = None


def _skip_retarget() -> bool:
    return os.environ.get(SKIP_RETARGET_ENV) == "1"


def prepare_harness(*, enable_proxy_if_needed: bool = True) -> HarnessSession:
    """Apply A0b/A0c. Idempotent. Honors an operator-set harness path."""
    global _active, _atexit_registered
    if _active is not None:
        return _active
    session = HarnessSession()
    _active = session
    if not _atexit_registered:
        atexit.register(_atexit_restore)
        _atexit_registered = True
    if _skip_retarget():
        session.notes.append("skipped")
        return session

    operator_path = os.environ.get(HARNESS_PATH_ENV)
    if operator_path:
        session.notes.append("operator_harness_path")
        _apply_sdk_monkeypatches(session, patched_binary=Path(operator_path))
        return session

    stock = stock_harness_path()
    if stock is None:
        session.notes.append("no_stock_binary")
        _apply_sdk_monkeypatches(session, patched_binary=None)
        _maybe_start_proxy(session, enable=enable_proxy_if_needed)
        return session

    if not binary_contains_withdrawn(stock):
        session.notes.append("stock_already_live")
        return session

    dest = cache_dir() / stock.name
    try:
        write_patched_copy(stock, dest)
        if binary_contains_withdrawn(dest):
            session.notes.append("copy_patch_failed")
        elif (unrunnable := smoke_check_harness(dest)) is not None:
            # Adopting a copy that cannot start would trade a withdrawn-model
            # failure for a harder-to-diagnose stdio one. Fall through to the
            # site-packages / proxy fallback below instead.
            session.notes.append(f"copy_patch_unrunnable:{unrunnable}")
        else:
            session.patched_binary = dest
            os.environ[HARNESS_PATH_ENV] = str(dest)
            session.set_harness_path = True
            session.notes.append("copy_patch")
            _apply_sdk_monkeypatches(session, patched_binary=dest)
            return session
    except OSError as exc:
        session.notes.append(f"copy_patch_error:{type(exc).__name__}")

    _apply_sdk_monkeypatches(session, patched_binary=session.patched_binary)
    if os.environ.get(NO_SITE_PACKAGES_ENV) != "1":
        backup = overwrite_site_packages_harness(stock)
        if backup is not None:
            session.site_backup = backup
            session.notes.append("site_packages_overwrite")
            if not binary_contains_withdrawn(stock):
                return session

    still_withdrawn = binary_contains_withdrawn(stock)
    if still_withdrawn:
        _maybe_start_proxy(session, enable=enable_proxy_if_needed)
    return session


def restore_harness() -> None:
    global _active
    if _active is None:
        return
    _active.close()
    _active = None


def _atexit_restore() -> None:
    restore_harness()


def _apply_sdk_monkeypatches(session: HarnessSession, *, patched_binary: Path | None) -> None:
    """Wrap SDK internals so the harness path/config carries the live id."""
    module: Any = sys.modules.get(_LOCAL_CONNECTION)
    if module is None:
        try:
            module = importlib.import_module(_LOCAL_CONNECTION)
        except ImportError:
            return

    restores: list[Callable[[], None]] = []
    original_path = getattr(module, "_get_default_binary_path_external", None)
    if patched_binary is not None and callable(original_path):

        def _patched_path() -> str:
            return str(patched_binary)

        module._get_default_binary_path_external = _patched_path
        restores.append(lambda: setattr(module, "_get_default_binary_path_external", original_path))

    original_models = getattr(module, "build_models_proto", None)
    if callable(original_models):

        def _patched_models(models: Any) -> Any:
            rewritten = []
            for target in models:
                name = getattr(target, "name", None)
                if isinstance(name, str) and WITHDRAWN_INPUT_DETECTION_MODEL in name:
                    target = target.model_copy(update={"name": rewrite_withdrawn_model_text(name)})
                rewritten.append(target)
            return original_models(rewritten)

        module.build_models_proto = _patched_models
        restores.append(lambda: setattr(module, "build_models_proto", original_models))

    def _restore() -> None:
        for restore in reversed(restores):
            restore()

    if restores:
        session.monkeypatch_restore = _restore


def apply_binary_path_monkeypatch(module: Any, *, patched_binary: Path) -> Callable[[], None]:
    """Test helper: patch ``_get_default_binary_path_external`` on a stub."""
    original = getattr(module, "_get_default_binary_path_external", None)

    def _patched() -> str:
        return str(patched_binary)

    module._get_default_binary_path_external = _patched

    def _restore() -> None:
        if original is None:
            delattr(module, "_get_default_binary_path_external")
        else:
            module._get_default_binary_path_external = original

    return _restore


def overwrite_site_packages_harness(stock: Path) -> Path | None:
    """Last filesystem resort. Backup next to the original before overwrite."""
    if os.environ.get(NO_SITE_PACKAGES_ENV) == "1":
        return None
    stock_mode = stock.stat().st_mode
    backup = stock.with_name(stock.name + BACKUP_SUFFIX)
    original = stock.read_bytes()
    if not backup.is_file():
        backup.write_bytes(original)
        backup.chmod(stock_mode)
        if backup.read_bytes() != original:
            backup.unlink(missing_ok=True)
            raise OSError("site-packages harness backup failed verification")
    patched = patch_harness_bytes(original)
    if patched == original:
        return None
    stock.write_bytes(patched)
    stock.chmod(stock_mode)
    # Re-sign after patching to fix the invalidated code signature.
    with suppress(OSError, subprocess.CalledProcessError):
        subprocess.run(  # nosec B603 B607 - fixed argv, codesign is a system binary
            ["codesign", "-s", "-", "--force", "--preserve-metadata=entitlements", str(stock)],
            check=True,
            capture_output=True,
        )
    return backup


def restore_site_packages_backup(backup: Path) -> None:
    if not backup.is_file() or not backup.name.endswith(BACKUP_SUFFIX):
        return
    original = backup.with_name(backup.name[: -len(BACKUP_SUFFIX)])
    shutil.copy2(backup, original)
    backup.unlink(missing_ok=True)


def restore_site_packages_backups(stock: Path | None = None) -> str:
    """``agyloop doctor --repair-harness``: restore ``*.agyloop-bak`` copies."""
    target = stock or stock_harness_path()
    if target is None:
        return "no bundled localharness found"
    backup = target.with_name(target.name + BACKUP_SUFFIX)
    if not backup.is_file():
        return f"no backup at {backup}"
    restore_site_packages_backup(backup)
    return f"restored {target} from {backup.name}"


def _maybe_start_proxy(session: HarnessSession, *, enable: bool) -> None:
    if not enable or rewrite_proxy_disabled():
        session.notes.append("proxy_disabled")
        return
    proxy = GeminiRewriteProxy()
    try:
        url = proxy.start()
    except OSError as exc:
        session.notes.append(f"proxy_error:{type(exc).__name__}")
        return
    session.proxy = proxy
    os.environ.setdefault("HTTP_PROXY", url)
    os.environ.setdefault("HTTPS_PROXY", url)
    session.notes.append("rewrite_proxy")
    _LOG.warning(
        "gemini.rewrite_proxy.enabled",
        extra={"url": url, "rewrite": WITHDRAWN_INPUT_DETECTION_MODEL},
    )


def select_harness_path(
    *,
    operator_path: str | None,
    patched: Path | None,
) -> str | None:
    """Prefer an operator-set path; otherwise the patched copy."""
    if operator_path:
        return operator_path
    if patched is not None:
        return str(patched)
    return None
