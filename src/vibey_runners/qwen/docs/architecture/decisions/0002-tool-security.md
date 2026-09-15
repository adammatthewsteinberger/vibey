# ADR 0002: Treat model output as untrusted

All model tool calls cross typed validation and a worktree boundary. Secrets,
destructive commands, network access, execution time, and output size are
restricted. Every proposal, rejection, and result is appended to the run
ledger.

