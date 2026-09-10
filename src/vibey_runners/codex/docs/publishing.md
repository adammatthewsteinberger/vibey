# Publishing

`codexloop` ships via [Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
(OIDC). No long-lived PyPI API tokens are stored in GitHub.

## Environments

| GitHub Environment | Index | Branch / workflow |
|---|---|---|
| `testpypi` | https://test.pypi.org | **`develop`** → `.github/workflows/publish-testpypi.yml` |
| `pypi` | https://pypi.org | **`main`** → `.github/workflows/release-please.yml` (`publish-pypi`) |

Create them once (repo **Settings → Environments**), or via API as in the
setup checklist below.

## One-time Trusted Publisher setup

Do this **before** the first upload (pending publisher), signed in as the PyPI
owner account.

### TestPyPI

1. Open https://test.pypi.org/manage/account/publishing/
2. Add a pending publisher:
   - **PyPI Project Name:** `codexloop`
   - **Owner:** `adammatthewsteinberger`
   - **Repository name:** `codexloop`
   - **Workflow name:** `publish-testpypi.yml`
   - **Environment name:** `testpypi`

### PyPI

1. Open https://pypi.org/manage/account/publishing/
2. Add a pending publisher:
   - **PyPI Project Name:** `codexloop`
   - **Owner:** `adammatthewsteinberger`
   - **Repository name:** `codexloop`
   - **Workflow name:** `release-please.yml`
   - **Environment name:** `pypi`

## Release flow

```text
feat/* ──PR──► develop ──auto TestPyPI──► main ──release-please──► PyPI
```

1. Land work on `develop`. Every push to `develop` runs **Publish TestPyPI**
   (`publish-testpypi.yml`). Do not publish TestPyPI from `main`.
2. Smoke-install from TestPyPI if needed:
   `pip install -i https://test.pypi.org/simple/ --pre codexloop`.
3. Merge `develop` → `main` when ready.
4. `release-please` opens a release PR against **`main` only**
   (`target-branch: main` in `.github/workflows/release-please.yml`).
5. Squash-merge the release PR → GitHub Release + tag → `publish-pypi`
   uploads to **PyPI**. Do not open or merge `chore(develop): release …` PRs.

Manual PyPI retry (Trusted Publishing, `main` / tagged release only):

```bash
gh workflow run release-please.yml -f publish_to_pypi=true
```

Manual TestPyPI from `develop`:

```bash
gh workflow run "Publish TestPyPI" --ref develop
```

## Local dry-run (no upload)

```bash
python -m build
twine check --strict dist/*
```
