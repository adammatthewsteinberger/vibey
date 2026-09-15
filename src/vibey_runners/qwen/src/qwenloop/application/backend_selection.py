# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Deterministic backend selection."""

from dataclasses import dataclass

from qwenloop.domain.model import Backend


@dataclass(frozen=True, slots=True)
class Hardware:
    system: str
    nvidia_vram_bytes: int = 0


@dataclass(frozen=True, slots=True)
class BackendChoice:
    backend: Backend
    reason: str


def select_backend(
    requested: Backend, hardware: Hardware, *, vllm_installed: bool
) -> BackendChoice:
    if requested is not Backend.AUTO:
        return BackendChoice(requested, "explicit configuration")
    if hardware.system == "Linux" and hardware.nvidia_vram_bytes >= 40 * 1024**3 and vllm_installed:
        return BackendChoice(Backend.VLLM, "Linux NVIDIA GPU has at least 40 GiB usable VRAM")
    return BackendChoice(Backend.LLAMA_CPP, "portable backend for this hardware")
