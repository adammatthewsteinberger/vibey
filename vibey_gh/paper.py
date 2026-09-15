# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Render docs/paper.md as a journal-class LaTeX document (#185).

The doctrine: every repository's documentation also produces a research paper that a
real journal could accept — produced always as Markdown → LaTeX → PDF, liberal with
LaTeX mathematics, and preformatted to an established venue's exact requirements. This
module is the MD → LaTeX stage, targeting IEEEtran (conference two-column by default,
`journal` on request) because IEEEtran ships with every TeX Live and its layout rules
are the requirements of a real, established publisher — the artifact is
submission-shaped by construction.

Stdlib only, like the book exporter: the converter handles the constrained markdown
this family's docs actually use, passes `$...$`, `$$...$$`, and ```latex fences through
untouched so the source can be as liberal with LaTeX as the doctrine demands, and the
LaTeX → PDF compile belongs to the workflow (TeX Live), never to this package's
dependency list.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

__all__ = ["PaperError", "convert", "render_paper"]


class PaperError(RuntimeError):
    """The paper cannot be rendered and the reason is actionable."""


_SPECIALS = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
    "$": r"\$",
}
_SPECIALS_RE = re.compile("|".join(re.escape(k) for k in _SPECIALS))


def _escape(text: str) -> str:
    return _SPECIALS_RE.sub(lambda m: _SPECIALS[m.group(0)], text)


_MATH_SPLIT = re.compile(r"(\$\$.*?\$\$|\$[^$\n]+\$)", re.DOTALL)
_INLINE = [
    (re.compile(r"\*\*(.+?)\*\*"), r"\\textbf{\1}"),
    (re.compile(r"\*(.+?)\*"), r"\\emph{\1}"),
    (re.compile(r"\[(.+?)\]\((.+?)\)"), r"\1\\footnote{\\url{\2}}"),
]
_CODE_SPAN = re.compile(r"`([^`]+)`")


def _inline(text: str) -> str:
    """Inline markdown to LaTeX, with math spans passed through untouched.

    Order is the correctness here: math is split out FIRST so `$O(n^2)$` is never
    escaped; code spans are lifted second so backticked text is never bolded; the
    remaining prose is escaped and then styled.
    """
    parts = _MATH_SPLIT.split(text)
    out: list[str] = []
    for i, part in enumerate(parts):
        if i % 2 == 1:  # a math span, verbatim
            out.append(part)
            continue
        spans: list[str] = []

        def lift(match: re.Match[str], spans: list[str] = spans) -> str:
            spans.append(match.group(1))
            return f"\x00{len(spans) - 1}\x00"

        lifted = _CODE_SPAN.sub(lift, part)
        escaped = _escape(lifted)
        for pattern, repl in _INLINE:
            escaped = pattern.sub(repl, escaped)
        for j, span in enumerate(spans):
            escaped = escaped.replace(f"\x00{j}\x00", rf"\texttt{{{_escape(span)}}}")
        out.append(escaped)
    return "".join(out)


@dataclass
class _Doc:
    title: str = ""
    abstract: list[str] = None  # type: ignore[assignment]
    body: list[str] = None  # type: ignore[assignment]
    bibliography: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        self.abstract = []
        self.body = []
        self.bibliography = []


def convert(markdown: str) -> _Doc:
    """The constrained conversion: headings, prose, lists, tables, code, math, refs.

    `# Title` names the paper; a paragraph opening `**Abstract**` becomes the abstract;
    `## References` with a list becomes `thebibliography`; ```latex fences are emitted
    raw — the doctrine's LaTeX-liberal channel; everything else is the markdown the
    docs already write.
    """
    doc = _Doc()
    lines = markdown.splitlines()
    i = 0
    in_refs = False
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            lang = line[3:].strip()
            block: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                block.append(lines[i])
                i += 1
            i += 1
            if lang == "latex":
                doc.body.extend(block)
            else:
                doc.body.append(r"\begin{verbatim}")
                doc.body.extend(block)
                doc.body.append(r"\end{verbatim}")
            continue
        if line.startswith("$$"):
            doc.body.append(line)
            i += 1
            # A one-line display equation opens and closes on the same line; only a
            # multi-line block consumes further lines, and only until its own closer.
            if not (len(line) > 2 and line.rstrip().endswith("$$")):
                while i < len(lines):
                    doc.body.append(lines[i])
                    i += 1
                    if lines[i - 1].rstrip().endswith("$$"):
                        break
            continue
        if line.startswith("# ") and not doc.title:
            doc.title = _inline(line[2:].strip())
        elif line.startswith("## "):
            heading = line[3:].strip()
            in_refs = heading.lower() == "references"
            if not in_refs:
                doc.body.append(rf"\section{{{_inline(heading)}}}")
        elif line.startswith("### "):
            doc.body.append(rf"\subsection{{{_inline(line[4:].strip())}}}")
        elif re.match(r"^\s*[-*]\s+", line):
            item = re.sub(r"^\s*[-*]\s+", "", line)
            if in_refs:
                doc.bibliography.append(_inline(item))
            else:
                if not doc.body or not doc.body[-1].startswith("\\item"):
                    doc.body.append(r"\begin{itemize}")
                doc.body.append(rf"\item {_inline(item)}")
                if i + 1 >= len(lines) or not re.match(r"^\s*[-*]\s+", lines[i + 1]):
                    doc.body.append(r"\end{itemize}")
        elif (
            line.startswith("|")
            and i + 1 < len(lines)
            and set(lines[i + 1].replace("|", "").strip()) <= {"-", " ", ":"}
        ):
            header = [c.strip() for c in line.strip("|").split("|")]
            rows: list[list[str]] = []
            i += 2
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip("|").split("|")])
                i += 1
            spec = "l" * len(header)
            doc.body.append(rf"\begin{{tabular}}{{{spec}}}")
            doc.body.append(r"\hline")
            doc.body.append(" & ".join(_inline(c) for c in header) + r" \\ \hline")
            for row in rows:
                doc.body.append(" & ".join(_inline(c) for c in row) + r" \\")
            doc.body.append(r"\hline")
            doc.body.append(r"\end{tabular}")
            continue
        elif re.match(r"\s*\*\*Abstract\b", line):
            text = re.sub(r"^\s*\*\*Abstract[.:]?\*\*[.:]?\s*", "", line.strip())
            para = [text] if text else []
            i += 1
            while i < len(lines) and lines[i].strip():
                para.append(lines[i].strip())
                i += 1
            doc.abstract.append(_inline(" ".join(para)))
            continue
        elif line.strip():
            doc.body.append(_inline(line))
        else:
            doc.body.append("")
        i += 1
    if not doc.title:
        raise PaperError("paper.md needs a `# Title` heading")
    if not doc.abstract:
        raise PaperError("paper.md needs a paragraph opening with **Abstract**")
    return doc


def render_paper(markdown: str, author: str, journal: bool = False, keywords: str = "") -> str:
    """The full IEEEtran document for docs/paper.md."""
    doc = convert(markdown)
    mode = "journal" if journal else "conference"
    parts = [
        rf"\documentclass[{mode}]{{IEEEtran}}",
        r"\usepackage{amsmath,amssymb,amsthm}",
        r"\usepackage{algorithmic}",
        r"\usepackage{url}",
        r"\newtheorem{theorem}{Theorem}",
        r"\newtheorem{invariant}{Invariant}",
        r"\newtheorem{lemma}{Lemma}",
        r"\begin{document}",
        rf"\title{{{doc.title}}}",
        rf"\author{{\IEEEauthorblockN{{{_escape(author)}}}}}",
        r"\maketitle",
        r"\begin{abstract}",
        *doc.abstract,
        r"\end{abstract}",
    ]
    if keywords:
        parts += [r"\begin{IEEEkeywords}", _escape(keywords), r"\end{IEEEkeywords}"]
    parts += doc.body
    if doc.bibliography:
        parts.append(rf"\begin{{thebibliography}}{{{len(doc.bibliography)}}}")
        for n, entry in enumerate(doc.bibliography, 1):
            parts.append(rf"\bibitem{{ref{n}}} {entry}")
        parts.append(r"\end{thebibliography}")
    parts.append(r"\end{document}")
    return "\n".join(parts) + "\n"
