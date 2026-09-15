# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Pinned model profiles. Digests are operator-verifiable manifest fields."""

from qwenloop.domain.model import Backend, ModelProfile

QWEN_REVISION = "65784b8b67c59e1ae00b0f85206ac78775a2a2f4"
QWEN_GGUF_REVISION = "d0a692ef765eefbf2fabb130b3cb2e8917e3d225"

PORTABLE = ModelProfile(
    name="qwen2.5-coder-14b-q5-k-m",
    backend=Backend.LLAMA_CPP,
    repository="Qwen/Qwen2.5-Coder-14B-Instruct-GGUF",
    revision=QWEN_GGUF_REVISION,
    filename="qwen2.5-coder-14b-instruct-q5_k_m.gguf",
    sha256="98ab25e0132e3f1e6d3554e1b64de2b5021908819b740d9c208430117e49a775",
    size=10_508_873_152,
    quantization="Q5_K_M",
)

NVIDIA_BF16 = ModelProfile(
    name="qwen2.5-coder-14b-bf16",
    backend=Backend.VLLM,
    repository="Qwen/Qwen2.5-Coder-14B-Instruct",
    revision=QWEN_REVISION,
    filename=None,
    sha256=None,
    size=29_600_000_000,
    quantization="BF16",
)

PROFILES = {profile.name: profile for profile in (PORTABLE, NVIDIA_BF16)}
