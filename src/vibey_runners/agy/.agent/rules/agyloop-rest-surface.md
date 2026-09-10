# agyloop-rest-surface (Antigravity mirror of `.claude/skills/agyloop-rest-surface/SKILL.md`)


# agyloop REST surface (generated)

`agyloop api` is generated from Gemini REST discovery with a CI drift gate
(ADR 0015). Do not hand-write individual endpoints or the gate is meaningless.

- Developer lane: `GOOGLE_API_KEY` as a query parameter. Treat it as secret.
- Vertex lane is separate; doctor never guesses when both look possible.
- Baseline JSON lives under `src/agyloop/infrastructure/api/`.
- `--json` / file inlining for request bodies.

See `docs/guides/rest-api-surface.md`.
