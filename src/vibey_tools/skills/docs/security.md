# Security

The canonical policy is
[SECURITY.md](https://github.com/adammatthewsteinberger/vibey-skills/blob/main/SECURITY.md).

## Reporting

Use GitHub's [private vulnerability reporting](https://github.com/adammatthewsteinberger/vibey-skills/security/advisories/new).
Please do not open a public issue for a suspected vulnerability.

## What counts as a security issue here

This project ships **instructions that agents act on**, which widens the definition beyond
ordinary code:

- Guidance in a `SKILL.md` that would lead an agent to write insecure code, weaken a
  control, or exfiltrate data.
- A command, snippet, or configuration that is destructive or unsafe as written.
- Anything that looks like a real credential, private hostname, or internal identifier.
- Prompt-injection content aimed at a model reading these files.

A wrong technical claim is a normal bug — open an issue. A claim that would cause harm if
followed is a security report.
