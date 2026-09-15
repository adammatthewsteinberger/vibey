# Security policy

## Reporting a vulnerability

Do not open a public issue for a vulnerability. Use the repository's
[private security advisory form](https://github.com/adammatthewsteinberger/qwenloop/security/advisories/new).

Include the affected version, backend, operating system, reproduction, impact,
and suggested mitigation. Remove credentials, private source code, prompts, and
model outputs that contain sensitive material.

## Security boundaries

Qwenloop treats model output, repository content, tool output, and retrieved
content as untrusted. Model servers bind to loopback and use per-launch bearer
credentials. Filesystem writes remain inside the assigned worktree, and model
weights are installed only after an explicit operator command.
