// LaTeX on the documentation site. Loaded before MathJax only when `[documentation] math`
// is on; release-surfaces serves a pinned, checksummed MathJax from the site itself, so a
// reader's browser never fetches a third-party CDN to read an equation (doctrines 8.a, 10.a).
//
// Two kinds of LaTeX reach a page:
// 1. Inline `$...$` and display `$$...$$` math. pymdownx.arithmatex protects it from the
//    Markdown pass and wraps it in `.arithmatex` elements; MathJax typesets only those.
// 2. ```latex fences, which the research paper uses for theorem-like environments that a
//    TeX engine renders natively. A browser cannot, so they are turned into styled blocks
//    here — `\begin{invariant}[Name] ... \end{invariant}` becomes "Invariant (Name). ..."
//    with its math typeset — and a `verbatim` environment becomes a code block. Anything
//    else is left as the LaTeX source it is, never guessed at.
(() => {
  "use strict";

  const ENVIRONMENTS = {
    invariant: "Invariant",
    theorem: "Theorem",
    lemma: "Lemma",
    definition: "Definition",
    proposition: "Proposition",
    corollary: "Corollary",
    proof: "Proof",
  };

  const escapeHtml = (text) =>
    text.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

  // TeX's text ligatures, applied only to prose, never inside math: `---` is an em dash,
  // `--` an en dash, `~` a non-breaking space.
  const texProse = (text) =>
    escapeHtml(text).replace(/---/g, "\u2014").replace(/--/g, "\u2013").replace(/~/g, "\u00a0");

  // `$...$` inside a converted environment becomes `\(...\)`, which MathJax typesets.
  const inlineMath = (text) =>
    text
      .split(/(\$[^$]+\$)/)
      .map((part, i) =>
        i % 2 === 1
          ? `<span class="arithmatex">\\(${escapeHtml(part.slice(1, -1))}\\)</span>`
          : texProse(part),
      )
      .join("");

  const counters = {};

  const convert = (code) => {
    const source = code.textContent.trim();
    const verbatim = source.match(/^\\begin\{verbatim\}([\s\S]*?)\\end\{verbatim\}$/);
    if (verbatim) {
      const pre = document.createElement("pre");
      const inner = document.createElement("code");
      inner.textContent = verbatim[1].trim();
      pre.append(inner);
      return pre;
    }
    const env = source.match(/^\\begin\{(\w+)\}(?:\[([^\]]*)\])?([\s\S]*?)\\end\{\1\}$/);
    if (!env || !(env[1] in ENVIRONMENTS)) {
      return null;
    }
    const [, name, title, body] = env;
    counters[name] = (counters[name] || 0) + 1;
    const block = document.createElement("div");
    block.className = `latex-env latex-${name}`;
    const label = name === "proof" ? ENVIRONMENTS[name] : `${ENVIRONMENTS[name]} ${counters[name]}`;
    const heading = `<strong>${label}${title ? ` (${inlineMath(title)})` : ""}.</strong> `;
    const paragraphs = body.trim().split(/\n\s*\n/).map((p) => inlineMath(p.replace(/\s+/g, " ")));
    block.innerHTML = `<p>${heading}${paragraphs.join("</p><p>")}</p>`;
    return block;
  };

  const convertLatexFences = () => {
    document.querySelectorAll("pre > code.language-latex, pre > code.latex").forEach((code) => {
      const replacement = convert(code);
      if (replacement) {
        code.parentElement.replaceWith(replacement);
      }
    });
  };

  window.MathJax = {
    tex: {
      inlineMath: [["\\(", "\\)"]],
      displayMath: [["\\[", "\\]"]],
      processEscapes: false,
      processEnvironments: true,
    },
    options: {
      ignoreHtmlClass: ".*|",
      processHtmlClass: "arithmatex",
    },
    svg: { fontCache: "global" },
    startup: {
      pageReady: () => {
        convertLatexFences();
        return window.MathJax.startup.defaultPageReady();
      },
    },
  };
})();
