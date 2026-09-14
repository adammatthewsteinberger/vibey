# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Explicit, resumable model installation and verification."""

import hashlib
import json
import os
import urllib.request
from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path
from typing import BinaryIO

from platformdirs import user_cache_path

from qwenloop.domain.model import ModelProfile


class ModelCache:
    def __init__(
        self,
        root: Path | None = None,
        *,
        opener: Callable[..., BinaryIO] = urllib.request.urlopen,
    ) -> None:
        self.root = (root or user_cache_path("qwenloop")).resolve()
        self._opener = opener

    def profile_dir(self, profile: ModelProfile) -> Path:
        target = self.root / "models" / profile.name
        if target.is_symlink():
            raise ValueError(f"model directory must not be a symlink: {target}")
        return target

    def install(self, profile: ModelProfile) -> Path:
        if profile.filename is None:
            raise ValueError(
                "BF16 is installed and verified through the pinned vLLM/Hugging Face cache"
            )
        directory = self.profile_dir(profile)
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        target = directory / profile.filename
        partial = target.with_suffix(target.suffix + ".partial")
        start = partial.stat().st_size if partial.exists() else 0
        if profile.size is None or start != profile.size:
            url = (
                f"https://huggingface.co/{profile.repository}/resolve/{profile.revision}/"
                f"{profile.filename}?download=true"
            )
            request = urllib.request.Request(
                url, headers={"Range": f"bytes={start}-"} if start else {}
            )
            response = self._opener(request, timeout=120)
            mode = "ab" if start and getattr(response, "status", 200) == 206 else "wb"
            with partial.open(mode) as stream:
                while chunk := response.read(1024 * 1024):
                    stream.write(chunk)
                stream.flush()
                os.fsync(stream.fileno())
        digest = _sha256(partial)
        if profile.sha256 is not None and digest != profile.sha256:
            raise ValueError("downloaded model digest does not match the pinned manifest")
        if profile.size is not None and partial.stat().st_size != profile.size:
            raise ValueError("downloaded model size does not match the pinned manifest")
        partial.replace(target)
        manifest = {**asdict(profile), "backend": profile.backend.value, "installed_sha256": digest}
        (directory / "installed.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        (directory / "LICENSE.txt").write_text(
            "Qwen2.5-Coder-14B-Instruct is licensed under Apache License 2.0.\n",
            encoding="utf-8",
        )
        return target

    def verify(self, profile: ModelProfile) -> Path:
        if profile.filename is None:
            raise ValueError("verify the BF16 snapshot through the pinned vLLM cache")
        directory = self.profile_dir(profile)
        target = directory / profile.filename
        manifest_path = directory / "installed.json"
        if not target.is_file() or not manifest_path.is_file():
            raise FileNotFoundError(f"model is not installed: {target}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("revision") != profile.revision:
            raise ValueError("installed model revision does not match the pinned profile")
        if _sha256(target) != manifest.get("installed_sha256"):
            raise ValueError("installed model digest does not match its installation manifest")
        return target


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()
