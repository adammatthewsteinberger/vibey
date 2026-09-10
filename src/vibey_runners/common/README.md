# vibey-runners-common

Shared `application/interfaces` and `application/usecases` for the AI
coding-agent session-runner family: `claudeloop` (the original), and its
retargets `codexloop`, `cursorloop`, and `agyloop`.

Only the protocols and use-case orchestrations that genuinely converge
across the family live here. Each runner still owns its own domain layer,
its own vendor-specific concrete implementations (in `infrastructure/`),
and any interface or use case whose actual shape diverges enough between
runners that forcing a shared version would misrepresent one of them —
those stay local to the runner that needs them. See each runner's own
`application/interfaces/` and `application/usecases/` packages, and the
monorepo-merge extraction notes, for what was and wasn't pulled in here
and why.
