# Migrating to vibey-bootstrap 4.0.0

4.0.0 is a **rename-only** major release. `azure-bootstrap` is now
**`vibey-bootstrap`**, published under
[adammatthewsteinberger/vibey-bootstrap](https://github.com/adammatthewsteinberger/vibey-bootstrap)
(see [NOTICE.md](NOTICE.md) for the attribution history). No function, class,
signature, default, or environment variable changed — only the names you type
to install and import it.

| | 3.x | 4.0.0 |
|---|---|---|
| PyPI distribution | `azure-bootstrap` | `vibey-bootstrap` |
| Import package | `azure_bootstrap` | `vibey_bootstrap` |
| Console script | `azbootstrap` | `vibey-bootstrap` (`azbootstrap` kept as a deprecated alias) |
| GitHub | `TheViziusGroup/azure-bootstrap` | `adammatthewsteinberger/vibey-bootstrap` |
| Docs | `theviziusgroup.github.io/azure-bootstrap` | `adammatthewsteinberger.github.io/vibey-bootstrap` |

## Upgrade steps

1. Swap the dependency:

   ```bash
   pip uninstall azure-bootstrap
   pip install "vibey-bootstrap>=4,<5"
   ```

   Extras keep their names: `pip install 'vibey-bootstrap[alerts,fastapi,health]'`.

2. Rename the imports (a mechanical find-and-replace):

   ```bash
   # from azure_bootstrap import ...      →  from vibey_bootstrap import ...
   # from azure_bootstrap.alerts import … →  from vibey_bootstrap.alerts import …
   git grep -l azure_bootstrap | xargs sed -i 's/azure_bootstrap/vibey_bootstrap/g'
   ```

   ```python
   import vibey_bootstrap
   from vibey_bootstrap import initialize_application, get_bootstrap_logger
   ```

3. Rename the CLI in scripts and CI:

   ```bash
   azbootstrap list        →  vibey-bootstrap list
   azbootstrap scaffold …  →  vibey-bootstrap scaffold …
   ```

   `azbootstrap` still works in 4.x — it prints a one-line deprecation notice to
   stderr and then delegates to `vibey-bootstrap`. It will be removed in a
   future major release.

4. Update any pins, `requirements.txt`, `pyproject.toml`, Dockerfiles, and
   Helm/Terraform templates that reference the old distribution name.

5. If you filter or route logs by logger name, note that logger names derived
   from the package follow the rename (`azure_bootstrap.retry.<op>` →
   `vibey_bootstrap.retry.<op>`, and any `logging.getLogger(__name__)` inside
   the library). Environment variables — including `AZURE_BOOTSTRAP_ALLOW_RESET`
   — are **unchanged**.

## What did **not** change

- Every public symbol, its module path *below* the top-level package, and its
  behaviour. `vibey_bootstrap.alerts`, `vibey_bootstrap.transports`, … are the
  same modules as their `azure_bootstrap.*` counterparts in 3.0.1.
- All environment variables (`USE_MOCK_BOOTSTRAP`, `APPLICATIONINSIGHTS_CONNECTION_STRING`,
  `AZURE_APPCONFIG_*`, transport settings, …).
- All pip extras and their contents.
- Python support: 3.11+.

## Why a major bump for a rename?

Changing the import path is a breaking change for every consumer, so SemVer
requires a major. The old `azure-bootstrap` distribution on PyPI will not
receive further releases beyond a final pointer release; pin `vibey-bootstrap`
going forward.
