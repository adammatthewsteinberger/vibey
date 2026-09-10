# Generated OpenAI REST surface

`codexloop api …` is a **generated** 1:1 CLI over the installed `openai`
Python SDK resource tree. Commands are discovered by walking
`cached_property` descriptors on resource classes — no live client and no
credentials are required to render `--help`.

## Usage

```bash
codexloop api --help
codexloop api models list --help
codexloop api chat completions create --json '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"hi"}]}'
```

### Common options

| Option | Meaning |
|---|---|
| `--provider openai\|azure\|custom` | Select the SDK client class |
| `--base-url URL` | Override the API base URL |
| `--json '{…}'` | Inline JSON object merged into the call kwargs |
| `--json-file PATH` | JSON file; contents may start with `@/other/path` |
| `--raw` | Use `with_raw_response` |
| `--stream` | Use `with_streaming_response` |
| `--max-items N` | Auto-paginate list endpoints up to N items |

Scalar SDK parameters (strings, ints, floats, bools) are also exposed as
typed `--kebab-case` options. Nested TypedDict bodies stay in `--json`.

## Drift gate

`tests/infrastructure/api/test_drift.py` asserts:

1. Every discovered SDK method has a registered CLI command.
2. The discovered method set matches the committed
   `api_baseline.json` (additions *and* removals fail CI).
3. Local helpers (`parse` / `stream` / `webhooks.unwrap` / …) are
   individually enumerated — no silent omissions.

After upgrading `openai`, regenerate the baseline only when the new surface
is intentional:

```bash
python -c "from codexloop.infrastructure.api.introspect import *; ..."  # or re-run the M4 freeze script
```

## Providers

- **openai** — first-party `OpenAI` client (`OPENAI_API_KEY`).
- **azure** — `AzureOpenAI` (`AZURE_OPENAI_*` / `OPENAI_API_VERSION`).
- **custom** — `OpenAI` with `--base-url` or `OPENAI_BASE_URL`.

The binder always reflects the **class tree** of the selected client. Today
Azure inherits the full OpenAI resource tree; if a future client exposes a
smaller surface, only that surface is mounted.
