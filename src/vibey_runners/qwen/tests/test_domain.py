# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
import pytest

from qwenloop.application.backend_selection import Hardware, select_backend
from qwenloop.domain.config import QwenConfig, parse_config
from qwenloop.domain.model import Backend, CapacityKind, RunStatus, terminal_status


def test_default_config() -> None:
    assert parse_config({}) == QwenConfig()


def test_config_validation() -> None:
    with pytest.raises(ValueError):
        parse_config({"max_turns": 0})
    with pytest.raises(ValueError):
        parse_config({"idle_timeout_seconds": -1})
    with pytest.raises(ValueError):
        parse_config({"backend": "unknown"})


def test_backend_auto_requires_linux_large_gpu_and_vllm() -> None:
    assert (
        select_backend(Backend.AUTO, Hardware("Darwin"), vllm_installed=True).backend
        is Backend.LLAMA_CPP
    )
    selected = select_backend(Backend.AUTO, Hardware("Linux", 40 * 1024**3), vllm_installed=True)
    assert selected.backend is Backend.VLLM
    assert (
        select_backend(Backend.VLLM, Hardware("Darwin"), vllm_installed=False).backend
        is Backend.VLLM
    )


def test_capacity_outranks_completion() -> None:
    assert terminal_status(CapacityKind.LOCAL_BUSY, True) is RunStatus.FAILED
    assert terminal_status(CapacityKind.AVAILABLE, True) is RunStatus.COMPLETED
    assert terminal_status(CapacityKind.AVAILABLE, False) is RunStatus.RUNNING
