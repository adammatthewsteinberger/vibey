# ADR 0001: Dual local inference behind one port

Use one application inference port with llama.cpp and vLLM adapters. The
portable profile is the pinned official Q5_K_M GGUF at 32K context. Linux
NVIDIA systems with at least 40 GiB usable VRAM may select pinned BF16 vLLM.
Weights remain outside the repository and standard images.

