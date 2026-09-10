# Architecture overview

`claudeloop` is built as an **onion** (a.k.a. hexagonal / ports-and-adapters):
four concentric layers, with dependencies pointing strictly inward. The
practical reason for this — not ceremony — is that every hard decision the
runner makes ("is this rate limit waitable?", "how long do we wait?", "is the
task actually done?") is a pure function over plain value objects, which is
what makes near-100% test coverage an honest number instead of a mocking
exercise. See [`../plans/architecture-and-roadmap.md`](../plans/architecture-and-roadmap.md)
for the full design rationale this page distills.

## The four layers

```
src/claudeloop/
├── domain/           # innermost. pure — no I/O, no third-party imports, no async
├── application/       # ports (Protocols) + use cases; depends only on domain
├── infrastructure/    # adapters; the ONLY layer allowed to import anthropic /
│                       #   claude_agent_sdk / structlog / httpx / etc.
├── cli/                # Typer entry points
└── bootstrap.py        # composition root — the one module allowed to see every layer
```

| Layer | May import | May NOT import | Why |
|---|---|---|---|
| `domain` | stdlib only | `application`, `infrastructure`, `cli`, any third-party package | Every domain type must be constructible and testable with zero setup. If a domain test needs a fixture more complex than a dataclass literal, something has leaked in. |
| `application` | `domain`, stdlib, `typing.Protocol` | `infrastructure`, `cli`, `anthropic`, `claude_agent_sdk` | Ports are Protocols, not ABCs — application code never imports a concrete SDK type, only shapes it defines itself. |
| `infrastructure` | `domain`, `application`, third-party SDKs | `cli` | Adapters translate between the SDK's real types and the ports application code depends on. This is the only place `anthropic` or `claude_agent_sdk` may appear in an `import` statement. |
| `cli` | `bootstrap`, `application` (use cases only, via bootstrap) | `infrastructure` directly, `domain` internals it doesn't need | Commands parse args, call a use case, format output. They should be thin enough that testing them is mostly `CliRunner` snapshot tests. |
| `bootstrap` | everything | — | The single seam where a concrete `infrastructure` adapter gets wired into an `application` port. Nothing outside this file should know both a port name and its concrete implementation. |

## The rule is enforced, not aspirational

`import-linter` runs in CI (and in `pre-commit`) against two contracts defined
in `pyproject.toml`:

```toml
[[tool.importlinter.contracts]]
name = "Onion layering"
type = "layers"
layers = [
    "claudeloop.cli",
    "claudeloop.bootstrap",
    "claudeloop.application",
    "claudeloop.domain",
]

[[tool.importlinter.contracts]]
name = "Infrastructure only reachable from bootstrap"
type = "forbidden"
source_modules = ["claudeloop.domain", "claudeloop.application"]
forbidden_modules = ["claudeloop.infrastructure"]
```

A PR that adds `from claudeloop.infrastructure.agent import gateway` inside
`domain/loop.py` fails CI with a specific, named contract violation — not a
code-review nit someone might miss. See
[`decisions/0001-onion-architecture-with-import-linter.md`](decisions/0001-onion-architecture-with-import-linter.md)
for why this was chosen over convention-only layering.

## Where new code belongs — a quick test

Ask, in order:

1. **Does it need to talk to the filesystem, the network, the clock, or an
   SDK?** → `infrastructure/`, behind a port defined in `application/ports.py`.
2. **Is it a decision — a branch that determines what happens next — with no
   I/O of its own?** → `domain/`. If you can write its test as
   `assert f(some_dataclass) == SomeOtherDataclass`, it belongs here.
3. **Is it orchestration — calling a port, then feeding the result to a domain
   function, then calling another port?** → `application/`, as a use case or
   inside `runner.py`.
4. **Is it argument parsing or output formatting for a human at a terminal?**
   → `cli/`.

When in doubt, push logic **inward**. A `cli/` command that contains an
`if/elif` chain deciding what a rate-limit response means is a bug waiting to
happen — that decision belongs in `domain/classify.py`, where it can be
property-tested without spinning up a CLI process.

## Status

Milestones **M2–M5** from the architecture plan are implemented: autonomous
`run`/`resume`/`sessions`/`doctor`, resilient waiting (M3), the generated
`claudeloop api ...` REST surface with drift gate (M4), and release polish
including expanded `doctor` checks and packaging verification (M5).
`domain/` and `application/` carry a CI-enforced 100% test-coverage gate;
see [`ports-and-adapters.md`](ports-and-adapters.md) for adapter mapping and
[`../plans/architecture-and-roadmap.md`](../plans/architecture-and-roadmap.md)
for the original milestone definitions.
