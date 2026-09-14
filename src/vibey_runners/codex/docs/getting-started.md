# Getting started

## Install

```bash
pipx install codexloop
```

From a clone (contributors):

```bash
pip install -e ".[dev,docs]"
```

## Preflight

```bash
codexloop doctor
codexloop capacity
```

## Run a plan

```bash
codexloop run path/to/plan.md --max-turns 20
```

Default transport is `codex exec --json`. Optional `--transport app-server`
probes the experimental app-server and falls back to exec when unavailable.

!!! note "Roadmap"
    Live app-server interrupt/steer against production `codex` builds still
    tracks the experimental protocol; the shim-backed adapter is covered in CI.
