# Synthetic Codex JSONL fixtures

**SYNTHETIC.** These files are hand-authored from the documented `codex exec --json`
event shapes in research notes R4 (`thread.started`, `turn.started`, `item.*`,
`turn.completed` with `usage`, `turn.failed` with a 429 body). They are **not**
captures from a real `codex` binary.

TODO: replace each fixture with a real capture once a `codex` binary is available.

`huge_line.jsonl` is a small placeholder. The oversized line is generated at runtime
by `FAKE_CODEX_MODE=huge_line` so git does not store a multi-megabyte file.
