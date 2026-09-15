# codexloop-architecture (Antigravity mirror of `.claude/skills/codexloop-architecture/SKILL.md`)


# codexloop architecture

Dependencies point inward. `import-linter` enforces this in CI.

```
src/codexloop/
├── domain/           # PURE. stdlib only. No I/O, no async, no third-party.
├── application/      # Protocol ports + use cases. Imports domain + stdlib.
├── infrastructure/   # Adapters. ONLY layer that may import openai.
├── cli/              # Typer. Calls application via bootstrap.
└── bootstrap.py      # Composition root — the ONE module that sees every layer.
```

## Where does new code go?

1. Touches FS, network, clock, or an SDK? → `infrastructure/`, behind a
   `Protocol` in `application/interfaces/`. Never `import openai`
   elsewhere.
2. Pure decision, zero I/O? → `domain/`. Examples: `classify.py`,
   `waiting.py`, `completion.py`, `capacity.py`.
3. Orchestration (port → domain → port)? → `application/`.
4. Argument parsing / terminal formatting? → `cli/`.

When in doubt, push logic inward. `lint-imports` names the broken contract.

See ADR 0001.
