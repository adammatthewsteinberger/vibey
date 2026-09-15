# qwenloop

`qwenloop` is an autonomous, local Qwen 2.5 Coder 14B runner. It uses a
portable llama.cpp/Q5_K_M profile by default and can use BF16 through vLLM on
Linux NVIDIA systems with at least 40 GiB of usable VRAM.

Model installation is always explicit. The package, tests, `doctor`, and Vibey
integration never download model weights.

## Install

Until the first PyPI release, install the runner from the immutable Git tag or
an explicit commit:

```bash
uv tool install \
  'qwenloop @ git+https://github.com/adammatthewsteinberger/qwenloop.git@feature/qwenloop-local-engine'
```

The Python package never bundles model weights.

## Quick start

```bash
qwenloop model install --profile portable
qwenloop model verify
qwenloop doctor
qwenloop run plan.md --run-id <uuid> --cwd <worktree>
```

The stable run contract is `.qwenloop/runs/<run-id>/`, exit code `75` for a
graceful wind-down, the `QWENLOOP_TASK_FULLY_COMPLETE` marker, and a
`qwenloop-verdict` result fence.

## Inference profiles

| Profile | Backend | Intended hardware | Model installation |
|---|---|---|---|
| `portable` | llama.cpp Q5_K_M | Apple Silicon, Linux CPU, supported offload GPUs | Explicit `qwenloop model install --profile portable` |
| `nvidia-bf16` | vLLM BF16 | Linux NVIDIA with at least 40 GiB free VRAM | Operator-managed pinned Hugging Face/vLLM cache |

Servers bind to loopback and require a per-launch bearer token. Qwenloop never
silently changes backend during a run.

## Development

```bash
uv sync --extra dev
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict src/qwenloop
uv run lint-imports
uv run pytest -q
uv run bandit -q -r src/qwenloop
```

First-party code is held to 100% line and branch coverage. Model and hardware
smokes are deliberately separate from the hermetic CI suite.

## Release workflow

Qwenloop uses `develop` as its integration branch and `main` as its release
branch. `vibey-gh` provides provenance fingerprints, merge-train automation,
derived versions, promotion, and post-release branch realignment.

## License

Qwenloop is MIT licensed. Qwen2.5-Coder model artifacts are separately licensed
under Apache License 2.0 and are downloaded only after an explicit operator
command.
