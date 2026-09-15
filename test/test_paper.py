# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The research-paper pipeline (#185): MD -> journal-class LaTeX.

The contract is a real publisher's: IEEEtran class, math passed through untouched so
the source can be as LaTeX-liberal as the doctrine demands, prose escaped so a stray
underscore never breaks a build three steps downstream, and actionable refusals when
the paper lacks the parts a journal requires.
"""

from __future__ import annotations

import pytest

from vibey_gh import paper

MD = """# A Sound System

**Abstract.** We prove $T(n) = O(n)$ with 100% coverage & no _fuss_.

## Model

Inline $a < A$ math, **bold**, *emphasis*, `code_span`, and a [link](https://x.example).

$$E = mc^2$$

- first item
- second item

### Detail

| col_a | col_b |
|---|---|
| 1 | $x^2$ |

```latex
\\begin{theorem}Raw LaTeX passes.\\end{theorem}
```

```python
print("verbatim")
```

## References

- A. Author, *Work*, 2026.
- B. Writer, *Other*, 2025.
"""


def test_the_document_is_ieeetran_shaped():
    tex = paper.render_paper(MD, author="A. Person", keywords="k1; k2")
    assert tex.startswith(r"\documentclass[conference]{IEEEtran}")
    assert r"\usepackage{amsmath,amssymb,amsthm}" in tex
    assert r"\title{A Sound System}" in tex
    assert r"\IEEEauthorblockN{A. Person}" in tex
    assert r"\begin{abstract}" in tex
    assert r"\begin{IEEEkeywords}" in tex and "k1; k2" in tex
    assert tex.rstrip().endswith(r"\end{document}")


def test_journal_mode_switches_the_class_option():
    tex = paper.render_paper(MD, author="A", journal=True)
    assert tex.startswith(r"\documentclass[journal]{IEEEtran}")


def test_math_passes_through_untouched():
    """The LaTeX-liberal channel: $...$ and $$...$$ reach the .tex byte-for-byte."""
    tex = paper.render_paper(MD, author="A")
    assert "$T(n) = O(n)$" in tex
    assert "$a < A$" in tex
    assert "$$E = mc^2$$" in tex
    assert "$x^2$" in tex


def test_prose_is_escaped_but_styled():
    tex = paper.render_paper(MD, author="A")
    assert r"coverage \& no \_fuss\_" in tex
    assert r"\textbf{bold}" in tex and r"\emph{emphasis}" in tex
    assert r"\texttt{code\_span}" in tex
    assert r"\footnote{\url{https://x.example}}" in tex


def test_structures_render_as_their_latex_counterparts():
    tex = paper.render_paper(MD, author="A")
    assert r"\section{Model}" in tex and r"\subsection{Detail}" in tex
    assert r"\begin{itemize}" in tex and r"\item first item" in tex
    assert r"\begin{tabular}{ll}" in tex and r"col\_a & col\_b" in tex
    assert r"\begin{theorem}Raw LaTeX passes.\end{theorem}" in tex
    assert r"\begin{verbatim}" in tex and 'print("verbatim")' in tex


def test_references_become_thebibliography():
    tex = paper.render_paper(MD, author="A")
    assert r"\begin{thebibliography}{2}" in tex
    assert r"\bibitem{ref1}" in tex and r"\bibitem{ref2}" in tex
    assert r"\section{References}" not in tex


@pytest.mark.parametrize(
    ("source", "missing"),
    [("no title\n\n**Abstract.** a\n", "Title"), ("# T\n\nbody only\n", "Abstract")],
)
def test_a_paper_missing_journal_essentials_is_refused(source, missing):
    with pytest.raises(paper.PaperError, match=missing):
        paper.render_paper(source, author="A")


def test_the_cli_writes_the_tex_and_reports_it(tmp_path, capsys):
    from vibey_gh import cli

    src = tmp_path / "paper.md"
    src.write_text(MD)
    out = tmp_path / "out" / "paper.tex"
    code = cli.main(["paper", "--source", str(src), "--output", str(out), "--author", "A. Person"])
    assert code == 0
    assert "paper.tex" in capsys.readouterr().out
    assert out.read_text().startswith(r"\documentclass")


def test_the_cli_refuses_a_missing_source_actionably(tmp_path, capsys):
    from vibey_gh import cli

    code = cli.main(
        [
            "paper",
            "--source",
            str(tmp_path / "nope.md"),
            "--output",
            str(tmp_path / "o.tex"),
            "--author",
            "A",
        ]
    )
    assert code == 1
    assert "vibey-gh paper:" in capsys.readouterr().err


def test_multiline_display_math_and_abstract_are_consumed_exactly():
    md = (
        "# T\n\n**Abstract.** First line\ncontinues here.\n\n"
        "$$\n\\sum_{i=0}^{n} i\n$$\n\nAfter math.\n"
    )
    tex = paper.render_paper(md, author="A")
    assert "\\sum_{i=0}^{n} i" in tex
    assert "First line continues here." in tex
    assert "After math." in tex


def test_two_lists_open_and_close_independently():
    md = "# T\n\n**Abstract.** A.\n\n- a\n- b\n\nprose\n\n- c\n"
    tex = paper.render_paper(md, author="A")
    assert tex.count(r"\begin{itemize}") == 2
    assert tex.count(r"\end{itemize}") == 2


def test_a_paper_without_references_gets_no_bibliography():
    md = "# T\n\n**Abstract.** A.\n\nBody.\n"
    tex = paper.render_paper(md, author="A")
    assert r"\begin{thebibliography}" not in tex


def test_an_unterminated_display_block_ends_at_the_file_not_in_a_loop():
    md = "# T\n\n**Abstract.** A.\n\n$$\n\\alpha + \\beta\n"
    tex = paper.render_paper(md, author="A")
    assert "\\alpha + \\beta" in tex
