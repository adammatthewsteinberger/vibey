# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""mkdocs hooks.

Removes the literate-nav nav file from the built site.

`docs/gen_reference.py` writes `reference/.nav.md` through mkdocs-gen-files so the nav for
644 generated skill pages needs no mkdocs.yml edit. mkdocs-literate-nav consumes that file to
build the nav, but because gen-files adds it as a *virtual* page, mkdocs also renders it,
leaving an orphan page nothing links to.

Two documented approaches were tried and neither works for virtual files:

  * `exclude_docs: reference/.nav.md` — applies to real files in docs_dir; gen-files adds
    its pages afterwards, so the pattern never matches. Verified: orphan still built.
  * dot-prefixing the filename — mkdocs skips dot-prefixed files it discovers on disk, but
    not ones a plugin injects. Verified: `.nav.md` was rendered to `reference/.nav/`.

Deleting the rendered output after the build is therefore the reliable option, and it is
honest about what it does: the nav has already been constructed by then, so nothing depends
on the file still being present.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

log = logging.getLogger("mkdocs.hooks")

# Every stem literate-nav might have been pointed at, so renaming nav_file cannot silently
# start leaving an orphan behind again.
NAV_STEMS = (".nav", "SUMMARY")


def on_post_build(config, **kwargs) -> None:
    site = Path(config["site_dir"])
    removed = []
    for stem in NAV_STEMS:
        for path in list(site.rglob(stem)) + list(site.rglob(f"{stem}.html")):
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            removed.append(str(path.relative_to(site)))
    if removed:
        log.info("hooks: removed orphan nav page(s): %s", ", ".join(sorted(removed)))
