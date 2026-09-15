# Deterministic Lexical Retrieval for Agent Skill Libraries: Budgeted Context Packets with Verifiable Provenance

**Abstract.** Agent skill libraries face a context-economics problem: a library of
hundreds of long-form reference documents cannot be loaded wholesale into a model's
context window, yet fragmentary retrieval of safety- and correctness-critical guidance
is worse than none. We present a retrieval design for a 644-document skill corpus in
which indexing is a *deterministic, content-addressed* function of the corpus —
$\mathrm{index} = f(\mathrm{corpus})$, bit-stable across runs — retrieval returns only
*complete* heading-bounded sections with exact source provenance (path, line range,
content hash), and packet assembly under a token budget $B$ *fails closed*: when the
mandatory rule set $M$ for a request exceeds $B$, the assembler returns
`budget_insufficient` rather than a truncated rule. The engine is standard-library-only,
makes no network calls, and its security posture (parameterized FTS5 queries, symlink
containment, secret redaction) is enforced by tests. We state the determinism and
fail-closed properties, describe the evaluation harness, and argue the lexical baseline
must be judged on cost per accepted work item, not retrieval metrics alone.

## Introduction

Let the corpus be $S = \{s_1, \dots, s_n\}$, $n = 644$ skill documents across $127$
plugins, each a long-form, source-cited reference designed for model consumption. Loading
all of $S$ costs $\Theta(\sum_i |s_i|)$ tokens — orders beyond any context window — while
loading none forfeits exactly the guidance an agent is most likely to get confidently
wrong. Retrieval-augmentation is the standard answer, but its usual failure modes are
disqualifying here: nondeterministic indexes defeat review; fragment-level chunks split a
rule from its exceptions; and best-effort truncation silently deletes the sentence that
mattered.

## Design invariants

```latex
\begin{invariant}[Deterministic indexing]
The index is a pure function of the corpus: identical corpus bytes yield identical
manifests, chunk identifiers, and scores across machines and runs. All content is
hash-addressed; the manifest records corpus and per-section hashes.
\end{invariant}
```

Determinism makes retrieval *reviewable*: a packet's manifest names the exact corpus
state, so a reviewer can reproduce any selection decision byte-for-byte.

```latex
\begin{invariant}[Complete sections only]
The retrieval unit is a heading-bounded Markdown section, returned whole, with its
source-relative path, line range, and content hash. No sub-section fragment is ever
emitted.
\end{invariant}
```

```latex
\begin{invariant}[Fail-closed budgeting]
For a packet request with mandatory content $M$ and budget $B$: if
$\mathrm{tokens}(M) > B$, assembly returns \texttt{budget\_insufficient}; the assembler
never truncates a mandatory section to fit. Low-scoring optional content is omitted and
the omission is recorded in the manifest.
\end{invariant}
```

The manifest also carries `low_confidence`, directing the caller to fall back to native
full-skill activation — degradation is explicit and machine-readable, never silent.

## Architecture

Indexing parses frontmatter and headings from every
`plugins/*/skills/*/SKILL.md`, producing `manifest.json` (content-addressed) and
`index.sqlite3` — metadata plus an FTS5 full-text table queried exclusively with bound
parameters. A packet request is a versioned JSON object (objective, requirements,
acceptance criteria, language and path signals, plugin/skill allow- and deny-lists,
`maximum_context_tokens`); strict mode rejects unknown fields, so a misspelled
constraint is an error rather than an ignored wish.

## Security posture

The threat model is a local tool touching untrusted file trees: FTS5 queries are
parameterized (injection-resistant by construction and by test); symlinked skill sources
and index directories fail closed rather than escaping the boundary; secrets matching
common credential shapes are redacted from packet output; and the index path is
URI-escaped before SQLite `file:` open so hostile path characters cannot redirect the
read. Each property is pinned by a unit test in `tests/test_context_engine.py`.

## Evaluation

The harness scores retrieval against a gold case set: for each case, the expected
skills and the packet's selections yield standard set metrics
$$P = \frac{|R \cap E|}{|R|}, \qquad R_c = \frac{|R \cap E|}{|E|}$$
with per-case selection reasons recorded for error analysis. We treat these as
*diagnostics*, not the objective: the deployment criterion is cost per accepted work
item — a packet that halves token spend but raises rework is a regression, and the
manifest's provenance fields exist precisely so such regressions can be traced to the
selections that caused them.

## Related work

Dense-vector retrieval dominates the literature but reintroduces nondeterminism
(embedding versions, ANN indexes) that defeats the reviewability invariant; we treat it
as a candidate refinement to be admitted only if it wins on the deployment criterion.
The exact-head release calculus and ledger-mediated orchestration papers (companion
repositories) govern how this engine's outputs enter production.

## Conclusion

For agent skill libraries, determinism, whole-section retrieval, and fail-closed
budgeting turn retrieval from a stochastic accelerant into an auditable system
component: every packet names exactly what it contains, where every byte came from, and
what it chose to leave out.

## References

- SQLite, *FTS5 Extension*, https://www.sqlite.org/fts5.html.
- vibey-gh, *Exact-Head Evaluation*, companion paper, 2026.
- vibey, *Ledger-Mediated Orchestration*, companion paper, 2026.
- This repository: docs/rag-context-engine.md and tests/test_context_engine.py, 2026.
