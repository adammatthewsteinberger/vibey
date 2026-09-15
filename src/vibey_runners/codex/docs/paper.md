# Taxonomy-Faithful Capacity Classification: Never Reading `insufficient_quota` as a Window

**Abstract.** OpenAI's error taxonomy hands an autonomous runner a specific trap: two
adjacent error codes — `rate_limit_exceeded` (a reopening window) and
`insufficient_quota` (an empty balance) — arrive through the same HTTP status family
and similar prose, yet demand opposite responses. Treating the second as the first is
an unbounded hang; treating the first as the second abandons a run that one bounded
wait would have saved. We present codexloop's classification discipline — the family's
window-versus-credit invariant made **taxonomy-faithful**: classification keys on the
vendor's own machine-readable error codes before any prose lexicon, prose is a
fallback with pessimistic defaults, and the generated OpenAI SDK surface keeps the
code set current. The family core — bounded runs, never blocking, ledger resumption,
capacity-outranks-completion — is instantiated unchanged over the Codex/GPT transport.

## Introduction

The transplant thesis (the claudeloop paper) confines vendor variance to lexicons and
transports. codexloop's variance is concentrated in one high-stakes cell of the
lexicon: OpenAI's own taxonomy distinguishes the waitable from the unwaitable, and the
runner's job is to *refuse to be cleverer than the taxonomy* — while surviving the
cases where prose arrives without a code.

## Code-first classification

$$\kappa(e) = \begin{cases} \mathsf{window} & e.\mathrm{code} = \texttt{rate\_limit\_exceeded} \\ \mathsf{credits} & e.\mathrm{code} = \texttt{insufficient\_quota} \\ \mathrm{lexicon}(e.\mathrm{text}) & e.\mathrm{code}\ \mathrm{absent} \end{cases}$$

```latex
\begin{invariant}[Taxonomy fidelity]
When the vendor supplies a machine-readable error code, classification uses it and
only it — prose lexicons never override a code. The prose path exists solely for
codeless failures, and its unknown-text default is $\mathsf{credits}$: pessimism is
the only safe reading of an unclassified failure.
\end{invariant}
```

The waitability consequences are the family's: $\mathsf{window}$ enters a
deadline-bounded probe capped by $W_{\max}$; $\mathsf{credits}$ fails fast with the
reason in the ledger.

## The generated SDK surface

The runner ships a generated OpenAI SDK CLI; generation keeps the error-code set and
endpoint surface current with the vendor, so taxonomy fidelity does not rot into
prose-guessing as the vendor evolves. The family's drift discipline (agyloop's gate)
applies: divergence between the committed surface and the published one is a red
build, not a runtime surprise.

## The shared core

Unchanged from the family: runs admitted only under the explicit bound vector (turns,
dollars, per-turn watchdog, stall watchdog, maximum wait) with preemptive budget
stops; no execution path blocks on stdin; resumption from the append-only ledger
alone, $\mathrm{state}(t) = f(\mathrm{ledger}_{\leq t})$, with git savepoints and a
run-guarded `unwind`; and completion only by agreement of independent evidence under
**capacity outranks completion**.

## References

- claudeloop, *The Transplantable Session Runner* — the family core this instantiates, 2026.
- cursorloop, *Capacity-Outranks-Completion*; agyloop, *Quota-Aware Autonomy* — sibling papers, 2026.
- OpenAI API documentation: error code taxonomy (`rate_limit_exceeded`, `insufficient_quota`).
- This repository: docs/getting-started.md and the decision records, 2026.
