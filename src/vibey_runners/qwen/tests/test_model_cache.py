# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
import io
from dataclasses import replace
from pathlib import Path

import pytest

from qwenloop.infrastructure.model_cache import ModelCache
from qwenloop.infrastructure.profiles import PORTABLE


class Response(io.BytesIO):
    status = 200


def test_explicit_install_and_verify(tmp_path: Path) -> None:
    content = b"model bytes"
    profile = replace(PORTABLE, size=len(content), sha256=None)
    cache = ModelCache(tmp_path, opener=lambda *_args, **_kwargs: Response(content))
    target = cache.install(profile)
    assert target.read_bytes() == content
    assert cache.verify(profile) == target
    target.write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="digest"):
        cache.verify(profile)


def test_model_cache_rejects_symlink_boundary(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    models = tmp_path / "models"
    models.mkdir()
    (models / PORTABLE.name).symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        ModelCache(tmp_path).profile_dir(PORTABLE)


def test_model_cache_rejects_bf16_direct_install(tmp_path: Path) -> None:
    from qwenloop.infrastructure.profiles import NVIDIA_BF16

    cache = ModelCache(tmp_path)
    with pytest.raises(ValueError, match="BF16"):
        cache.install(NVIDIA_BF16)
    with pytest.raises(ValueError, match="BF16"):
        cache.verify(NVIDIA_BF16)


def test_model_cache_verify_rejects_missing_manifest(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        ModelCache(tmp_path).verify(PORTABLE)


def test_model_cache_rejects_short_download(tmp_path: Path) -> None:
    cache = ModelCache(tmp_path, opener=lambda *_args, **_kwargs: Response(b"short"))
    profile = replace(PORTABLE, sha256=None)
    with pytest.raises(ValueError, match="size"):
        cache.install(profile)


def test_model_cache_publishes_complete_resumed_download_without_network(tmp_path: Path) -> None:
    content = b"complete partial"
    profile = replace(PORTABLE, size=len(content), sha256=None)
    partial = tmp_path / "models" / profile.name / f"{profile.filename}.partial"
    partial.parent.mkdir(parents=True)
    partial.write_bytes(content)

    def unexpected_network(*_args, **_kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("a complete partial must not make a network request")

    target = ModelCache(tmp_path, opener=unexpected_network).install(profile)

    assert target.read_bytes() == content


def test_model_cache_rejects_pinned_digest_and_revision(tmp_path: Path) -> None:
    content = b"model bytes"
    profile = replace(PORTABLE, size=len(content), sha256="0" * 64)
    cache = ModelCache(tmp_path, opener=lambda *_args, **_kwargs: Response(content))
    with pytest.raises(ValueError, match="pinned manifest"):
        cache.install(profile)

    valid = replace(PORTABLE, size=len(content), sha256=None)
    cache.install(valid)
    manifest = tmp_path / "models" / valid.name / "installed.json"
    text = manifest.read_text().replace(valid.revision, "wrong")
    manifest.write_text(text)
    with pytest.raises(ValueError, match="revision"):
        cache.verify(valid)
