# codexloop-rest-surface (Antigravity mirror of `.claude/skills/codexloop-rest-surface/SKILL.md`)


# codexloop REST surface

`codexloop api` generates a 1:1 CLI mirror of the OpenAI Python SDK's REST
methods. The tree is code-generated from the SDK itself, not maintained by
hand.

## api_baseline.json drift gate

`api_baseline.json` freezes the **OpenAI SDK's** method count and list,
not codexloop's. It is a snapshot of what the SDK exposes, not what
codexloop adds.

A test fails when:

- The SDK adds or removes methods (changes `method_count`).
- Methods appear or disappear from the `methods` list.
- `local_helpers` (like `chat.completions.stream`) change.

This gate prevents SDK upgrades from silently altering the API surface
without review.

## Refreshing the baseline

After an intentional SDK upgrade, refresh the baseline:

```bash
codexloop api --help  # generates the tree
# The test writes the new baseline to api_baseline.json
pytest tests/cli/test_api.py --update-baseline
```

Commit the updated `api_baseline.json` in the same PR as
`pyproject.toml` changes.

**Never refresh the baseline for unrelated PRs.** A drift failure
during SDK upgrade is expected and intentional — it forces you to
inspect what changed.
