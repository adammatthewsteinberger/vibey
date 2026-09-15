# vibey-skills

Formerly **vibe-engineering-skills** — see [NOTICE.md](https://github.com/adammatthewsteinberger/vibey-skills/blob/main/NOTICE.md).

**127 plugins. 644 Agent Skills.** Evidence-grounded practitioner references for the parts of
software engineering an agent is most likely to get confidently wrong: security, compliance,
cloud infrastructure, identity automation, DevSecOps, AI/ML, data engineering, frontend,
mobile, architecture, quality engineering, process, and technical writing.

"Vibe engineering" is the disciplined counterpart to vibe coding — keeping an agent fast
*and* correct. These skills are the reference layer for that: each one is a long-form,
source-cited document rather than a prompt snippet, written so a model can act on it.

Beyond installation, the `vibey-skills` CLI ships a [retrieval context
engine](rag-context-engine.md): build a local index of every skill, search it, and
assemble budgeted context packets for an agent.

## Two ways to install

=== "Claude Code marketplace"

    ```bash
    /plugin marketplace add adammatthewsteinberger/vibey-skills
    /plugin install security-principles@vibey-skills
    ```

=== "PyPI (any agent)"

    ```bash
    uvx vibey-skills install --all
    ```

    Copies every skill into `~/.claude/skills`, which also works for any other harness
    that reads `SKILL.md`.

See [Installation](installation.md) for both routes in full, [Usage](usage.md) for the CLI,
and the [Skills reference](reference/index.md) for all 644 skills.

## What makes a skill here different

- **Sourced.** Claims cite the standard, vendor doc, or paper they come from.
- **Trigger-engineered.** A skill's `description` is the only thing a model sees when
  deciding whether to load it, so each one names the concrete tasks and terms that should
  activate it.
- **Self-contained.** No skill assumes another has been loaded.

## License

MIT, © 2026 The Vizius Group and Adam Matthew Steinberger. See
[LICENSE](https://github.com/adammatthewsteinberger/vibey-skills/blob/main/LICENSE) and
[NOTICE.md](https://github.com/adammatthewsteinberger/vibey-skills/blob/main/NOTICE.md) —
the project was originally developed at The Vizius Group as `vibe-engineering-skills` and is
republished here with their permission.

---

Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
