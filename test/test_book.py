# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Exporting the built docs site as a book (#137).

The contract under test is KDP's, not ours: an EPUB whose `mimetype` entry is first and
stored, a 3.0 package with Dublin Core metadata, chapters spined in nav order, and a
print HTML carrying the exact 6in x 9in trim — because "almost a valid EPUB" is a
rejection email three days after upload.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from vibey_gh import book

NAV = """site_name: demo
nav:
  - Home: index.md
  - Start here:
      - Welcome: start/index.md
  - Reference: reference.md
strict: true
"""

PAGE = "<html><body><nav>skip</nav><main><h1>T</h1><p>body<br></p><script>x()</script></main></body></html>"


def _site(tmp_path: Path) -> Path:
    site = tmp_path / "site"
    for page in ("index.html", "start/index.html", "reference/index.html"):
        target = site / page
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(PAGE)
    return site


def test_chapters_come_from_the_nav_in_order():
    chapters = book.chapters_from_nav(NAV)
    assert [c.source for c in chapters] == ["index.md", "start/index.md", "reference.md"]
    assert [c.title for c in chapters] == ["Home", "Welcome", "Reference"]
    # Nesting is recorded, order is never rearranged: the nav order IS the doctrine
    # order, and the book must inherit it untouched.
    assert [c.depth for c in chapters] == [0, 1, 0]


def test_a_navless_configuration_is_an_error_not_an_empty_book():
    with pytest.raises(book.BookError, match="no chapters"):
        book.chapters_from_nav("site_name: demo\nstrict: true\n")


def test_sources_map_to_the_built_sites_directory_urls():
    chapters = book.chapters_from_nav(NAV)
    assert chapters[0].site_page == "index.html"
    assert chapters[1].site_page == "start/index.html"
    assert chapters[2].site_page == "reference/index.html"


def test_readme_sources_are_index_pages():
    """mkdocs builds adr/README.md to adr/index.html — README is an index page, not a
    directory of its own. The third dogfooded deploy found this the hard way."""
    chapters = book.chapters_from_nav("nav:\n  - Decisions: adr/README.md\n  - Top: README.md\n")
    assert chapters[0].site_page == "adr/index.html"
    assert chapters[1].site_page == "index.html"


def test_extraction_takes_main_strips_chrome_and_closes_voids():
    body = book.extract_main(PAGE)
    assert "<h1>T</h1>" in body
    assert "script" not in body and "nav>" not in body
    assert "<br/>" in body, "a bare <br> is a hard error on a Kindle"


def test_extraction_falls_back_to_article_then_role_main_and_fails_on_none():
    assert "x" in book.extract_main("<article>x</article>")
    # The anchor the ProperDocs theme actually emits, discovered when the first
    # dogfooded deploy refused every page: a Bootstrap column carrying role="main",
    # with arbitrarily nested divs no regex can balance.
    themed = (
        '<body><div class="row"><div class="col-md-3"><nav>side</nav></div>'
        '<div class="col-md-9" role="main"><div class="inner"><h1>T</h1>'
        "<p>content</p></div></div></div><footer>f</footer></body>"
    )
    body = book.extract_main(themed)
    assert "<h1>T</h1>" in body and "content" in body
    assert "footer" not in body and "side" not in body
    with pytest.raises(book.BookError, match="role"):
        book.extract_main("<body>nothing</body>")


def test_the_epub_is_kdp_shaped(tmp_path):
    written = book.build_book(
        _site(tmp_path),
        NAV,
        tmp_path / "out",
        {"title": "Demo Book", "author": "A. Author", "publisher": "Pub", "description": "D"},
    )
    with zipfile.ZipFile(written["epub"]) as z:
        infos = z.infolist()
        # The byte-level contract readers sniff for: mimetype first, STORED.
        assert infos[0].filename == "mimetype"
        assert infos[0].compress_type == zipfile.ZIP_STORED
        assert z.read("mimetype") == b"application/epub+zip"
        container = z.read("META-INF/container.xml").decode()
        assert 'full-path="OEBPS/content.opf"' in container
        opf = z.read("OEBPS/content.opf").decode()
        for needle in (
            '<package version="3.0"',
            "<dc:title>Demo Book</dc:title>",
            "<dc:creator>A. Author</dc:creator>",
            "<dc:publisher>Pub</dc:publisher>",
            "urn:uuid:",
            'properties="nav"',
        ):
            assert needle in opf
        # Spine order is nav order.
        spine = opf.split("<spine>")[1]
        assert spine.index("index") < spine.index("start-index") < spine.index("reference")
        toc = z.read("OEBPS/toc.xhtml").decode()
        assert 'epub:type="toc"' in toc and "Welcome" in toc


def test_the_print_html_carries_the_kdp_trim(tmp_path):
    written = book.build_book(
        _site(tmp_path),
        NAV,
        tmp_path / "out",
        {"title": "Demo Book", "subtitle": "Sub", "author": "A. Author"},
    )
    text = written["print_html"].read_text()
    assert "size:6in 9in" in text and "margin:0.75in 0.5in" in text
    assert "font-size:11pt" in text
    assert "Table of Contents" in text and "Copyright" in text and "Sub" in text
    assert text.index('id="index"') < text.index('id="start-index"')


def test_a_missing_built_page_names_the_chapter(tmp_path):
    site = _site(tmp_path)
    (site / "reference" / "index.html").unlink()
    with pytest.raises(book.BookError, match="reference.md"):
        book.build_book(site, NAV, tmp_path / "out", {"title": "T", "author": "A"})


@pytest.mark.parametrize("missing", ["title", "author"])
def test_metadata_without_title_or_author_is_refused(tmp_path, missing):
    meta = {"title": "T", "author": "A"}
    meta.pop(missing)
    with pytest.raises(book.BookError, match=missing):
        book.build_book(_site(tmp_path), NAV, tmp_path / "out", meta)


def test_the_cli_builds_a_book_and_reports_the_paths(tmp_path, capsys, monkeypatch):
    from vibey_gh import cli

    site = _site(tmp_path)
    cfg = tmp_path / "properdocs.yml"
    cfg.write_text(NAV)
    code = cli.main(
        [
            "book",
            "--site-dir",
            str(site),
            "--config-file",
            str(cfg),
            "--output-dir",
            str(tmp_path / "book"),
            "--title",
            "Demo",
            "--author",
            "A.",
        ]
    )
    out = capsys.readouterr().out
    assert code == 0
    assert "book.epub" in out and "book-print.html" in out


def test_the_cli_reports_an_actionable_error(tmp_path, capsys):
    from vibey_gh import cli

    cfg = tmp_path / "properdocs.yml"
    cfg.write_text("site_name: x\n")
    code = cli.main(
        [
            "book",
            "--site-dir",
            str(tmp_path),
            "--config-file",
            str(cfg),
            "--output-dir",
            str(tmp_path / "book"),
            "--title",
            "T",
            "--author",
            "A",
        ]
    )
    assert code == 1
    assert "no chapters" in capsys.readouterr().err


def test_parser_edges_nested_strips_startend_voids_and_charrefs():
    """The extractor's less-traveled branches, orphaned when two green PRs squashed
    into one red develop: nested chrome subtrees (a form inside a nav), self-closing
    tags both inside capture and inside a strip, a non-strip end tag while stripping,
    void end tags, and entity/character references in prose."""
    page = (
        "<main>"
        "<nav>skip <form>deeper</form> <em>styled-skip</em> <img src='x'/> still-skipped</nav>"
        "<p>keep &amp; &#8594; <br/> this</p>"
        "</main>"
    )
    body = book.extract_main(page)
    assert "keep &amp; &#8594;" in body
    assert "<br/>" in body
    assert "skip" not in body and "deeper" not in body


def test_parser_ignores_content_after_capture_and_stray_end_tags():
    page = "<div><main><p>inside</p></main><p>after</p></div><em>tail</em>"
    body = book.extract_main(page)
    assert "inside" in body and "after" not in body and "tail" not in body
    # a stray end tag arriving before any capture begins is ignored
    assert "x" in book.extract_main("</div><article>x</article>")


def test_parser_handles_end_of_void_and_unclosed_capture():
    # explicit </br> end tags are void — never decrement capture depth
    body = book.extract_main("<main><p>a</p></br><p>b</p></main>")
    assert "a" in body and "b" in body
    # capture that never closes ends at EOF with what it gathered
    assert "tail-content" in book.extract_main("<main><p>tail-content</p>")
