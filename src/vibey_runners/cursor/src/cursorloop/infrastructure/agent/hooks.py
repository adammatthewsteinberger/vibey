# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Managed autonomy fragment for ``.cursor/hooks.json``.

Cursor hooks are file-based only. Scripts live under the run state dir; we
append (never replace) one command per managed event, record SHA-256 of the
original and merged bytes, and restore only when the on-disk hash still
matches what we wrote. A mid-run user edit wins. Exit 2 is never used —
autonomy hooks exist to ALLOW, and any other non-zero fails open.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import logging
import shlex
from pathlib import Path
from typing import Any

from cursorloop.domain.autonomy import autonomy_preamble
from cursorloop.domain.hooks_policy import (
    HOOK_SUCCESS_EXIT,
    MANAGED_EVENTS,
    allow_payload,
    preamble_injection_payload,
)

_LOGGER = logging.getLogger(__name__)

_STATE_NAME = "state.json"
_SCRIPTS_DIRNAME = "hooks"
_ORIGINAL_BACKUP = "hooks.json.original"
_STOP_CAPTURE = "stop-final.txt"
_HOOKS_RELATIVE = Path(".cursor") / "hooks.json"
_STATE_KEYS = (
    "hooks_original_sha256",
    "hooks_merged_sha256",
    "hooks_original_path",
    "hooks_existed",
)
_SCRIPT_MODE = 0o700
_HEREDOC = "CURSORLOOP_HOOK_JSON"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _encode(obj: dict[str, Any]) -> bytes:
    return (json.dumps(obj, indent=2) + "\n").encode()


def _script_emitting(payload: dict[str, str]) -> str:
    body = json.dumps(payload, ensure_ascii=True)
    return (
        "\n".join(
            [
                "#!/bin/sh",
                "cat >/dev/null",
                f"cat <<'{_HEREDOC}'",
                body,
                _HEREDOC,
                f"exit {HOOK_SUCCESS_EXIT}",
            ]
        )
        + "\n"
    )


def _stop_script(capture_path: Path) -> str:
    quoted = shlex.quote(str(capture_path))
    payload = json.dumps(allow_payload("stop"), separators=(",", ":"))
    return (
        "\n".join(
            [
                "#!/bin/sh",
                "umask 077",
                f"cat > {quoted}",
                f"printf '%s\\n' '{payload}'",
                f"exit {HOOK_SUCCESS_EXIT}",
            ]
        )
        + "\n"
    )


class ManagedHooks:
    """``HookManager`` that deep-merges a never-block fragment into hooks.json."""

    def __init__(self, workspace: Path, state_dir: Path) -> None:
        self._workspace = Path(workspace)
        self._state_dir = Path(state_dir)
        self._hooks_file = self._workspace / _HOOKS_RELATIVE
        self._scripts_dir = self._state_dir / _SCRIPTS_DIRNAME
        self._state_path = self._state_dir / _STATE_NAME
        self._backup_path = self._state_dir / _ORIGINAL_BACKUP
        self._stop_capture = self._state_dir / _STOP_CAPTURE

    def install(self) -> None:
        if self.is_installed() and not self._recorded_install_unapplied():
            return
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._scripts_dir.mkdir(parents=True, exist_ok=True)
        self._write_scripts()

        existed, original = self._snapshot_original()
        merged_bytes = _encode(self._merge(original))
        self._update_state(
            {
                "hooks_original_sha256": _sha256(original),
                "hooks_merged_sha256": _sha256(merged_bytes),
                "hooks_original_path": str(self._hooks_file),
                "hooks_existed": existed,
            }
        )
        self._hooks_file.parent.mkdir(parents=True, exist_ok=True)
        self._atomic_write(self._hooks_file, merged_bytes)

    def restore(self) -> bool:
        state = self._read_state()
        merged_hash = state.get("hooks_merged_sha256")
        if not isinstance(merged_hash, str):
            return False
        current = self._hooks_file.read_bytes() if self._hooks_file.exists() else b""
        current_hash = _sha256(current)
        original_hash = state.get("hooks_original_sha256")
        if isinstance(original_hash, str) and current_hash == original_hash:
            self._clear_hook_state()
            return True
        if current_hash != merged_hash:
            _LOGGER.warning(
                "leaving %s in place: on-disk SHA-256 no longer matches the "
                "merged bytes we wrote; a mid-run edit wins",
                self._hooks_file,
            )
            return False

        if state.get("hooks_existed"):
            if not self._backup_path.exists():
                _LOGGER.warning(
                    "original hooks backup missing; leaving %s in place",
                    self._hooks_file,
                )
                return False
            original = self._backup_path.read_bytes()
            expected = state.get("hooks_original_sha256")
            if isinstance(expected, str) and _sha256(original) != expected:
                _LOGGER.warning(
                    "original hooks backup hash mismatch; leaving %s in place",
                    self._hooks_file,
                )
                return False
            self._atomic_write(self._hooks_file, original)
        elif self._hooks_file.exists():
            self._hooks_file.unlink()

        self._clear_hook_state()
        return True

    def is_installed(self) -> bool:
        return isinstance(self._read_state().get("hooks_merged_sha256"), str)

    def _recorded_install_unapplied(self) -> bool:
        """True when state was recorded but hooks.json is still the original."""
        original_hash = self._read_state().get("hooks_original_sha256")
        if not isinstance(original_hash, str):
            return False
        current = self._hooks_file.read_bytes() if self._hooks_file.exists() else b""
        return _sha256(current) == original_hash

    def diff(self) -> str:
        original = self._hooks_file.read_bytes() if self._hooks_file.exists() else b""
        current_text = original.decode()
        merged_text = _encode(self._merge(original)).decode()
        if current_text == merged_text:
            return ""
        return "".join(
            difflib.unified_diff(
                current_text.splitlines(keepends=True),
                merged_text.splitlines(keepends=True),
                fromfile=str(self._hooks_file),
                tofile="hooks.json (cursorloop managed)",
            )
        )

    def _snapshot_original(self) -> tuple[bool, bytes]:
        """Keep an existing backup only when restore state is absent.

        A crash after mutating hooks.json can leave the merged file as the only
        on-disk copy of the workspace hooks. Overwriting ``hooks.json.original``
        in that window would discard the user's real original. After a
        successful restore the backup is unlinked, so the next install
        snapshots live ``.cursor/hooks.json``.
        """
        if self._backup_path.exists() and not self.is_installed():
            original = self._backup_path.read_bytes()
            return original != b"", original
        existed = self._hooks_file.exists()
        original = self._hooks_file.read_bytes() if existed else b""
        self._backup_path.write_bytes(original)
        return existed, original

    def _write_scripts(self) -> None:
        for event in MANAGED_EVENTS:
            path = self._scripts_dir / f"{event}.sh"
            if event == "beforeSubmitPrompt":
                body = _script_emitting(preamble_injection_payload(autonomy_preamble()))
            elif event == "stop":
                body = _stop_script(self._stop_capture)
            else:
                body = _script_emitting(allow_payload(event))
            path.write_text(body)
            path.chmod(_SCRIPT_MODE)

    def _command_for(self, event: str) -> str:
        script = self._scripts_dir / f"{event}.sh"
        try:
            return str(script.relative_to(self._workspace))
        except ValueError:
            return str(script)

    def _merge(self, original: bytes) -> dict[str, Any]:
        data: dict[str, Any]
        if original:
            try:
                parsed: object = json.loads(original)
            except json.JSONDecodeError:
                parsed = {}
            data = parsed if isinstance(parsed, dict) else {}
        else:
            data = {}
        if "version" not in data:
            data["version"] = 1
        hooks = data.get("hooks")
        if not isinstance(hooks, dict):
            hooks = {}
            data["hooks"] = hooks
        for event in MANAGED_EVENTS:
            entry = {"command": self._command_for(event)}
            existing = hooks.get(event)
            if not isinstance(existing, list):
                existing = []
                hooks[event] = existing
            if entry not in existing:
                existing.append(entry)
        return data

    def _read_state(self) -> dict[str, Any]:
        if not self._state_path.exists():
            return {}
        try:
            parsed: object = json.loads(self._state_path.read_text())
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}

    def _update_state(self, fields: dict[str, Any]) -> None:
        state = self._read_state()
        state.update(fields)
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._atomic_write(self._state_path, _encode(state))

    def _clear_hook_state(self) -> None:
        state = self._read_state()
        for key in _STATE_KEYS:
            state.pop(key, None)
        if state:
            self._atomic_write(self._state_path, _encode(state))
        elif self._state_path.exists():
            self._state_path.unlink()
        if self._backup_path.exists():
            self._backup_path.unlink()

    def _atomic_write(self, path: Path, data: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_bytes(data)
        tmp.replace(path)
