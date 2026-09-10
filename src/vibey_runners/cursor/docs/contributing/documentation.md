# Documentation

Published site:
[https://adammatthewsteinberger.github.io/cursorloop/](https://adammatthewsteinberger.github.io/cursorloop/)

Built with MkDocs Material and deployed from `main` by
[`.github/workflows/docs.yml`](https://github.com/adammatthewsteinberger/cursorloop/blob/main/.github/workflows/docs.yml)
to GitHub Pages.

```bash
pip install -e ".[docs]"
mkdocs serve
mkdocs build --strict
```

`mkdocs build --strict` fails on broken internal links — the same gate CI
runs before every Pages deploy.

## Link rules (GitHub / GitHub.io / PyPI)

- **In `docs/`** use repo-relative Markdown links between pages
  (`getting-started/installation.md`). MkDocs rewrites them for the site;
  they also work when browsing the tree on GitHub.
- **In `README.md`** (ships to PyPI) use **absolute** `https://` URLs for
  docs, license, and badges — relative paths break on pypi.org.
- **`[project.urls]`** in `pyproject.toml` already points Documentation at
  the GitHub.io root; keep that URL in sync with `site_url` in `mkdocs.yml`.
