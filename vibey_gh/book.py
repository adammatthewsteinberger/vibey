# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Export the published documentation as a book: an EPUB 3.0 and a print-ready HTML.

Docs trapped in a browser cannot be printed as a desk reference or published on Amazon
KDP without a reformatting step, which is exactly the step nobody performs (#137). This
module removes it: chapters come from the site nav — so the copy doctrine's ordering
(beginner tier first, engineering reference second, scholarly material last) carries into
the book untouched — content comes from the already-built site's pages, and the output is
KDP-shaped by construction: the EPUB is a valid 3.0 package with Dublin Core metadata,
and the print HTML carries the standard 6in x 9in trim with 0.75in/0.5in margins, ready
for a headless-Chromium print-to-PDF in a workflow.

Deliberately stdlib-only, like everything else in this package: the EPUB container is
plain zipfile work, the nav parser reads only the constrained `nav:` block this family's
site configurations use, and content extraction is anchored on the built page's <main>
element. The one step that genuinely needs a browser — HTML to PDF — is left to the
caller's workflow, where installing Playwright is one line; the package itself grows no
dependency for it.
"""

from __future__ import annotations

import datetime
import html as html_lib
import html.parser as html_parser
import re
import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "BookChapter",
    "BookError",
    "build_book",
    "chapters_from_nav",
    "extract_main",
]


class BookError(RuntimeError):
    """A book cannot be built and the reason is actionable by the operator."""


@dataclass(frozen=True)
class BookChapter:
    title: str
    source: str  # docs-relative markdown path from the nav, e.g. "start/index.md"
    depth: int = 0  # nav nesting level; section headers render deeper entries grouped

    @property
    def slug(self) -> str:
        return re.sub(r"[^a-z0-9]+", "-", self.source.removesuffix(".md").lower()).strip("-")

    @property
    def site_page(self) -> str:
        """The built page for this source, mirroring mkdocs' directory URLs.

        README.md is an index page exactly like index.md — mkdocs builds
        `adr/README.md` to `adr/index.html`, not `adr/README/index.html` —
        discovered when the third dogfooded deploy could not find the ADR chapter.
        """
        stem = self.source.removesuffix(".md")
        parts = stem.rsplit("/", 1)
        name = parts[-1]
        if name in ("index", "README"):
            prefix = parts[0] + "/" if len(parts) == 2 else ""
            return f"{prefix}index.html"
        return f"{stem}/index.html"


_NAV_ENTRY = re.compile(r"^(\s*)-\s+([^:]+?):\s*(\S+\.md)\s*$")
_NAV_SECTION = re.compile(r"^(\s*)-\s+([^:]+?):\s*$")


def chapters_from_nav(config_text: str) -> list[BookChapter]:
    """Parse the ordered chapter list out of a site configuration's `nav:` block.

    Not a YAML parser on purpose: this package carries no dependencies, and the nav
    blocks this family writes are a constrained shape — `- Title: file.md` entries,
    optionally nested one level under `- Section:` headers. Anything outside that shape
    is ignored rather than misread, and an empty result is an error the operator can
    act on, never an empty book.
    """
    chapters: list[BookChapter] = []
    in_nav = False
    nav_indent: int | None = None
    for line in config_text.splitlines():
        if re.match(r"^nav:\s*$", line):
            in_nav = True
            nav_indent = None
            continue
        if not in_nav:
            continue
        if line.strip() and not line.startswith(" ") and not line.startswith("-"):
            break  # a new top-level key ends the nav block
        entry = _NAV_ENTRY.match(line)
        if entry:
            indent = len(entry.group(1))
            if nav_indent is None:
                nav_indent = indent
            depth = 0 if indent <= nav_indent else 1
            chapters.append(
                BookChapter(title=entry.group(2).strip(), source=entry.group(3), depth=depth)
            )
    if not chapters:
        raise BookError("no chapters: the site configuration has no `- Title: file.md` nav entries")
    return chapters


_STRIP_TAGS = frozenset({"script", "nav", "aside", "form", "button"})
_VOID_TAGS = frozenset({"br", "hr", "img", "input", "meta", "link"})


class _MainExtractor(html_parser.HTMLParser):
    """Capture the subtree of the first <main>, <article>, or role="main" element.

    A parser, not a regex: the content element nests arbitrarily many <div>s (the
    ProperDocs theme wraps the body in a Bootstrap column carrying role="main"), and no
    regular expression balances that. Subtrees of chrome tags (script, nav, aside,
    form, button) are dropped during capture, and void elements are re-emitted
    self-closed because EPUB readers parse XHTML.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.out: list[str] = []
        self.depth = 0  # nesting inside the captured element; 0 = not capturing
        self.strip_depth = 0
        self.done = False

    def _is_target(self, tag: str, attrs: list[tuple[str, str | None]]) -> bool:
        return tag in ("main", "article") or ("role", "main") in [(k, v) for k, v in attrs]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self.done:
            return
        if self.depth == 0:
            if self._is_target(tag, attrs):
                self.depth = 1
            return
        if self.strip_depth:
            if tag in _STRIP_TAGS:
                self.strip_depth += 1
            return
        if tag in _STRIP_TAGS:
            self.strip_depth = 1
            return
        text = self.get_starttag_text() or f"<{tag}>"
        if tag in _VOID_TAGS and not text.rstrip().endswith("/>"):
            text = text.rstrip()[:-1] + "/>"
        self.out.append(text)
        if tag not in _VOID_TAGS:
            self.depth += 1

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self.done or self.depth == 0 or self.strip_depth:
            return
        self.out.append(self.get_starttag_text() or f"<{tag}/>")

    def handle_endtag(self, tag: str) -> None:
        if self.done or self.depth == 0:
            return
        if self.strip_depth:
            if tag in _STRIP_TAGS:
                self.strip_depth -= 1
            return
        if tag in _VOID_TAGS:
            return
        self.depth -= 1
        if self.depth == 0:
            self.done = True
            return
        self.out.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        if self.depth and not self.strip_depth and not self.done:
            self.out.append(data)

    def handle_entityref(self, name: str) -> None:
        self.handle_data(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self.handle_data(f"&#{name};")


def extract_main(page_html: str) -> str:
    """The chapter body from a built page.

    Anchored on <main>, <article>, or any element carrying role="main" -- the last is
    what the ProperDocs theme actually emits, discovered when the first dogfooded
    deploy refused every page. Chrome subtrees are stripped because a book has no
    runtime; void elements are self-closed because a bare <br> that every browser
    forgives is a hard error on a Kindle.
    """
    parser = _MainExtractor()
    parser.feed(page_html)
    body = "".join(parser.out).strip()
    if not body:
        raise BookError(
            'page has no <main>, <article>, or role="main" element to take a chapter from'
        )
    return body


_EPUB_CSS = """body{font-family:Georgia,serif;line-height:1.55;margin:1em}
h1,h2,h3{font-family:Georgia,serif;line-height:1.2}
pre{white-space:pre-wrap;font-size:.85em;background:#f4f4f4;padding:.75em}
code{font-size:.9em}
table{border-collapse:collapse;width:100%}
td,th{border:1px solid #999;padding:.35em;text-align:left;vertical-align:top}
"""

# The standard KDP paperback interior: 6in x 9in trim, 0.75in top/bottom and 0.5in
# side margins, 11pt serif body — lifted verbatim from a generator that has already
# passed KDP's printable-file review.
_PRINT_CSS = """@page{size:6in 9in;margin:0.75in 0.5in 0.75in 0.5in}
body{font-family:Georgia,serif;font-size:11pt;line-height:1.5;margin:0}
h1{page-break-before:always;font-size:20pt;line-height:1.2}
h2{font-size:14pt;margin:1.5em 0 .75em}
h3{font-size:12pt;margin:1.25em 0 .5em}
pre{white-space:pre-wrap;font-size:8.5pt;background:#f4f4f4;padding:.6em;page-break-inside:avoid}
table{border-collapse:collapse;width:100%;font-size:9.5pt;page-break-inside:avoid}
td,th{border:1pt solid #666;padding:.3em;text-align:left;vertical-align:top}
img{max-width:100%}
.title-page{page-break-after:always;text-align:center;padding-top:2.5in}
.copyright-page{page-break-after:always;font-size:9pt;padding-top:5in}
.toc{page-break-after:always}
"""


def _xhtml(title: str, body: str, css_href: str = "style.css") -> str:
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        "<!DOCTYPE html>\n"
        '<html xmlns="http://www.w3.org/1999/xhtml">\n'
        f"<head><title>{html_lib.escape(title)}</title>"
        f'<link rel="stylesheet" type="text/css" href="{css_href}"/></head>\n'
        f"<body>{body}</body>\n</html>\n"
    )


def _content_opf(meta: dict[str, str], chapters: list[BookChapter], now: str) -> str:
    manifest = ['<item id="css" href="style.css" media-type="text/css"/>']
    spine = []
    manifest.append(
        '<item id="toc" href="toc.xhtml" media-type="application/xhtml+xml" properties="nav"/>'
    )
    spine.append('<itemref idref="toc"/>')
    for chapter in chapters:
        manifest.append(
            f'<item id="{chapter.slug}" href="{chapter.slug}.xhtml"'
            ' media-type="application/xhtml+xml"/>'
        )
        spine.append(f'<itemref idref="{chapter.slug}"/>')
    e = html_lib.escape
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<package version="3.0" xmlns="http://www.idpf.org/2007/opf" unique-identifier="uid">\n'
        '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
        f'<dc:identifier id="uid">urn:uuid:{uuid.uuid4()}</dc:identifier>\n'
        f"<dc:title>{e(meta['title'])}</dc:title>\n"
        f"<dc:creator>{e(meta['author'])}</dc:creator>\n"
        f"<dc:language>{e(meta.get('language', 'en'))}</dc:language>\n"
        f"<dc:description>{e(meta.get('description', ''))}</dc:description>\n"
        f"<dc:publisher>{e(meta.get('publisher', meta['author']))}</dc:publisher>\n"
        f'<meta property="dcterms:modified">{now}</meta>\n'
        "</metadata>\n"
        "<manifest>\n" + "\n".join(manifest) + "\n</manifest>\n"
        "<spine>\n" + "\n".join(spine) + "\n</spine>\n"
        "</package>\n"
    )


def _toc_xhtml(chapters: list[BookChapter]) -> str:
    items = "\n".join(
        f'<li><a href="{c.slug}.xhtml">{html_lib.escape(c.title)}</a></li>' for c in chapters
    )
    return _xhtml(
        "Table of Contents",
        f'<nav epub:type="toc" xmlns:epub="http://www.idpf.org/2007/ops">'
        f"<h1>Table of Contents</h1><ol>\n{items}\n</ol></nav>",
    )


def build_book(
    site_dir: Path,
    config_text: str,
    output_dir: Path,
    meta: dict[str, str],
) -> dict[str, Path]:
    """Build book.epub and book-print.html from a built site and its nav.

    Returns the paths written. Raises BookError with the missing piece named when a nav
    chapter has no built page — a book silently missing a chapter is worse than no book.
    """
    if "title" not in meta or not meta["title"]:
        raise BookError("book metadata needs at least a title")
    if "author" not in meta or not meta["author"]:
        raise BookError("book metadata needs an author")
    chapters = chapters_from_nav(config_text)
    bodies: dict[str, str] = {}
    for chapter in chapters:
        page = site_dir / chapter.site_page
        if not page.is_file():
            raise BookError(f"nav names {chapter.source} but the built site has no {page}")
        bodies[chapter.slug] = extract_main(page.read_text(encoding="utf-8"))

    output_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    epub_path = output_dir / "book.epub"
    with zipfile.ZipFile(epub_path, "w") as z:
        # The EPUB contract: `mimetype` first, STORED, no extra field — readers sniff
        # bytes 30..58 of the archive for this exact string.
        z.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip", zipfile.ZIP_STORED)
        z.writestr(
            "META-INF/container.xml",
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<container version="1.0"'
            ' xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n'
            '<rootfiles><rootfile full-path="OEBPS/content.opf"'
            ' media-type="application/oebps-package+xml"/></rootfiles>\n'
            "</container>\n",
        )
        z.writestr("OEBPS/content.opf", _content_opf(meta, chapters, now))
        z.writestr("OEBPS/style.css", _EPUB_CSS)
        z.writestr("OEBPS/toc.xhtml", _toc_xhtml(chapters))
        for chapter in chapters:
            z.writestr(f"OEBPS/{chapter.slug}.xhtml", _xhtml(chapter.title, bodies[chapter.slug]))

    e = html_lib.escape
    toc_rows = "\n".join(f'<li><a href="#{c.slug}">{e(c.title)}</a></li>' for c in chapters)
    sections = "\n".join(f'<section id="{c.slug}">{bodies[c.slug]}</section>' for c in chapters)
    year = datetime.datetime.now(datetime.UTC).year
    print_path = output_dir / "book-print.html"
    print_path.write_text(
        "<!DOCTYPE html>\n<html><head><meta charset='utf-8'>"
        f"<title>{e(meta['title'])}</title><style>{_PRINT_CSS}</style></head><body>\n"
        f'<div class="title-page"><h1 style="page-break-before:auto">{e(meta["title"])}</h1>'
        + (f"<p>{e(meta['subtitle'])}</p>" if meta.get("subtitle") else "")
        + f"<p>{e(meta['author'])}</p></div>\n"
        f'<div class="copyright-page"><p>Copyright &#169; {year} {e(meta["author"])}.'
        f" All rights reserved.</p><p>{e(meta.get('publisher', meta['author']))}</p></div>\n"
        f'<div class="toc"><h1>Table of Contents</h1><ol>\n{toc_rows}\n</ol></div>\n'
        f"{sections}\n</body></html>\n",
        encoding="utf-8",
    )
    return {"epub": epub_path, "print_html": print_path}
