---
name: language-diagnostics-tooling-and-evolution
description: "Use when making a language usable and durable: what a good diagnostic contains and the rules for error messages, warnings, source locations; incremental compilation and IDE support (query-based compilation, salsa-style memoization, what the LSP needs from you); the compiler test pyramid and formal verification; standard library and ecosystem design; and language evolution — backward compatibility, editions as the best mechanism we have, governance (BDFL, committees, RFC processes), and multiple implementations."
---

# Programming Language Development: Diagnostics, Incremental Compilation and IDE Support, Testing, Standard Library, and Evolution

> **Part 4 of 5** of the *Programming Language Development* reference (plugin `programming-language-development`), covering §10–§14. Sibling skills: `language-design-parsing-and-types` (§0–§4), `language-irs-optimization-and-backends` (§5–§7), `language-runtimes-interpreters-and-jits` (§8–§9), `language-development-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §17 → `language-development-reference` for the currency snapshot and what goes stale first.

> **How to read this.** Reference, not tutorial. Sections are independent. Three markers:
> - **[DURABLE]** — theory, algorithms, or a lesson every language implementation has
>   independently learned. Does not expire.
> - **[VERSIONED]** — depends on a specific toolchain, standard, or project's current
>   state. Verify against its docs.
> - **[CONTESTED]** — competent language designers disagree, publicly and permanently.
>   Both cases given.
>
> **⚠️ GOTCHA** boxes mark the design mistakes that are cheap to make on day one and
> impossible to undo on day one thousand.
>
> **The framing that organizes everything below: a language is a set of promises you can
> never take back.** Syntax you can deprecate. Semantics you cannot. Every hard decision
> in this document is really the question *"what am I willing to be permanently
> responsible for?"* — and the languages people love and the languages people resent are
> distinguished mostly by how carefully their designers answered it early.

---

## §10. Diagnostics

**[DURABLE] Error messages are the compiler's primary user interface.** For most users,
most of the time, the compiler is a machine that produces errors. Rust and Elm changed
industry expectations here permanently, and every new language is now judged against them.

### 10.1 What a good diagnostic contains

```
error[E0308]: mismatched types                    ← stable, searchable code
  --> src/main.rs:4:18                            ← precise primary location
   |
 3 |     let x: u32 = 5;
   |            --- expected due to this type      ← SECONDARY span: the cause
 4 |     let y: String = x;
   |            ------   ^ expected `String`, found `u32`
   |            |
   |            expected due to this type
   |
help: try converting the value                    ← ACTIONABLE, ideally machine-applicable
   |
 4 |     let y: String = x.to_string();
   |                      ++++++++++++
```
The elements, in order of value: **precise primary span**, **secondary spans that explain
*why*** (this is the biggest differentiator — showing the *other* end of the conflict),
**plain language, no jargon-first**, **a concrete suggestion**, **machine-applicable fixes**
(so `--fix` and the IDE quick-fix work), and a **stable error code** with extended
documentation.

### 10.2 The rules

1. **Never cascade** (§2.3 → `language-design-parsing-and-types`). One root cause, one error.
2. **Say what was expected, not just what was found.**
3. **Point at the cause, not the symptom.** Type inference makes this genuinely hard: the
   error surfaces where unification fails, which may be far from the mistake. Bidirectional
   checking (§4.2 → `language-design-parsing-and-types`) helps because you know the expected type.
4. **Suggest, but only when confident.** A wrong suggestion is worse than none.
5. **Errors, warnings, and lints are different things** with different severity policies.
   Let users configure lints; don't let them disable soundness errors.
6. **Test your diagnostics.** Snapshot-test error output (rustc's `ui` tests, Elm's
   approach). Untested diagnostics rot immediately.

### 10.3 Warnings

**[DURABLE] Warnings that everyone ignores are worse than no warnings**, because they train
users to ignore output. Keep the default set small and high-precision; put the rest behind
opt-in lint groups; and provide a mechanism to acknowledge-and-silence a specific instance
(`#[allow]`, `// nolint`) so `-Werror` is survivable.

### 10.4 Source locations

Keep spans **everywhere** — in the AST, through desugaring, through IR, into debug info.
Macro-expanded code needs a *chain* of locations (expansion site plus definition site) or
macro errors become unintelligible; Rust's `SyntaxContext`/expansion-info machinery exists
entirely for this. **This is much harder to add later than to design in.**

---

## §11. Incremental Compilation and IDE Support

### 11.1 The requirement has changed

**[DURABLE] A modern language needs a language server, and a batch compiler cannot become
one by accident.** The IDE's requirements are qualitatively different from the batch
compiler's:

| Batch compiler | Language server |
|---|---|
| Complete, valid input | **Always-broken input** |
| Whole program | One file changed, answer in <100 ms |
| Throughput | **Latency** |
| Correct errors | Best-effort answers, always |
| Can exit | Long-running, memory-bounded |

Two architectural answers: **one engine serving both** (rust-analyzer converging with
rustc; Roslyn; the TypeScript compiler) or **two implementations** (which guarantees
divergent behaviour and double the bug surface). The first is right and expensive.

### 11.2 The techniques

- **Query-based / demand-driven architecture.** Instead of running phases in order, express
  everything as memoized queries (`type_of(def)`, `resolve(name)`) over a dependency graph;
  on change, invalidate transitively and recompute only what's needed. This is rustc's
  query system and rust-analyzer's **salsa**, and it is the dominant design.
- **Red-green / persistent trees** (§2.4 → `language-design-parsing-and-types`) for cheap structural sharing across edits.
- **Firewalls**: hash intermediate results so that a change that doesn't alter a result
  stops propagating (reformatting a function body shouldn't invalidate its callers).
- **Laziness**: don't type-check function bodies you weren't asked about.
- **Interning** everything (strings, types, spans) so comparison is pointer equality.

**[DURABLE] Design your compiler as a query system from the beginning.** Retrofitting
incrementality onto a phase-ordered compiler is one of the largest refactors a compiler
team can undertake, and several major projects have spent years on it.

### 11.3 What the LSP needs from you

Completion (on broken input, ranked), go-to-definition, find-references (needs a
reverse index), hover types, rename (needs to know *every* reference, including in
macros and strings-that-are-code), diagnostics on the fly, signature help, semantic
highlighting, code actions, formatting, and inlay hints. **Each one is a query your
compiler must be able to answer about a partial program.**

---

## §12. Testing and Verification

### 12.1 The test pyramid for a compiler

- **Unit tests** per pass.
- **Snapshot/golden tests**: source in, expected output (IR, diagnostics, or machine code)
  out. Cheap, high-coverage, and the standard for diagnostics.
- **Execution tests**: compile and run, check behaviour. The real correctness signal.
- **Differential testing**: compare against another implementation or another optimization
  level. `-O0` vs `-O2` disagreement is a miscompile, full stop.
- **Metamorphic testing**: semantically equivalent programs must behave identically.
- **Fuzzing**: **Csmith** (random valid C generation) and **YARPGen** found hundreds of
  bugs in GCC and LLVM. **Alive2** does translation validation for LLVM peepholes — proving
  optimizations correct with an SMT solver. **If you have an optimizer, you need a fuzzer.**
- **Bootstrap tests**: compile the compiler with itself, compare stage2 and stage3 output.
  Byte-identical output is a strong signal.
- **Test suite reuse**: a new implementation of an existing language should run the
  existing conformance suite.

### 12.2 Formal verification

- **CompCert** — a formally verified C compiler in Coq. **The Yang et al. Csmith study
  found zero miscompiles in CompCert's verified middle end while finding hundreds in GCC
  and LLVM.** This is the strongest empirical evidence in the field for verification.
- **CakeML** — a verified ML compiler with a verified bootstrap.
- **Translation validation** — verify each *compilation run* rather than the compiler
  (Alive2). Far cheaper than full verification and applicable to existing compilers.
- **Mechanized semantics**: K framework, Redex, Lean/Coq formalizations. Even partially
  formalizing your semantics finds design bugs.

**[DURABLE] Full verification is expensive and mostly reserved for safety-critical
domains. Translation validation and fuzzing give most of the assurance for a fraction of
the cost** and should be in any serious compiler's CI.

---

## §13. Standard Library and Ecosystem

**[DURABLE] A language is not a language; it's a language plus a standard library plus a
package manager plus a build tool plus a formatter plus a debugger plus documentation.**
The languages that succeeded in the last twenty years shipped the whole thing (Go, Rust);
the ones that struggled left it to the community and got fragmentation.

**Standard library scope [CONTESTED]:** "batteries included" (Python, Go) versus minimal
core plus ecosystem (Rust, Node). *For batteries*: no dependency for common tasks, one
obvious way, no supply-chain risk for basics. *Against*: **the standard library is where
code goes to die** — you can never break it, you can never move fast, and Python's
`asyncio`/`urllib`/`distutils` history is the standard evidence. Rust's deliberate
minimalism trades a large dependency graph for the ability to evolve.

**Ship on day one**: a formatter (**with no options** — `gofmt` ended a category of
argument permanently), a build tool and package manager (see the package-manager reference),
a test runner, a documentation generator, a linter, and a debugger story (DWARF, and
actually test it).

---

## §14. Language Evolution

### 14.1 Backward compatibility

**[DURABLE] The core tension: every language must evolve, and every change breaks someone.**
The strategies actually used:
- **Never break** (Java, C, Go 1.x). Maximum trust, permanent accumulation of mistakes.
- **Deprecate then remove** (Python 2→3). The Python 3 transition took roughly a decade and
  is the field's canonical warning about breaking changes at scale.
- **Editions/language versions** (Rust editions, C++ standards). §14.2.
- **Feature flags** (`from __future__ import`, `#![feature]`). Lets you ship unstable
  features to consenting users and get feedback before committing.

### 14.2 Editions — the best mechanism we have

**Rust's edition model**: each crate declares its edition; editions may change syntax and
idioms; **crates of different editions interoperate freely** in one program because the
change happens in the front end and the IRs unify. Combined with `cargo fix` for automated
migration, this lets a language change `async` from an identifier to a keyword without a
Python-3 event.

**[DURABLE] If you're designing a language and you expect to live for decades, design the
edition mechanism early.** The constraint it imposes — editions cannot change the *type
system* or the *runtime*, only surface syntax and lints — is exactly the constraint that
makes it work, and it's much easier to honour from the start.

### 14.3 Governance

Options: BDFL (fast, coherent, has a bus factor and a succession crisis — Python's PEP 8016
governance transition after Guido's resignation is the reference), committee (ISO C/C++ —
slow, stable, produces documents rather than implementations), foundation + teams (Rust,
Python post-2018), corporate (Go, Swift, Kotlin — fast and coherent, with the community's
influence bounded by the sponsor's interests).

**[VERSIONED] The C++ committee's 2025–26 record is an instructive case**: C++26 was
finalized on 28 March 2026 after a six-day London meeting with 210 experts from 24 nations,
delivering reflection, contracts, `std::execution`, and a hardened standard library. It
also **rejected the "Safe C++" borrow-checking proposal** in favour of the Profiles
approach, and **the `[[profiles::enforce]]` attribute was then deferred to C++29**. Herb
Sutter stepped down as convener. Read that sequence as a demonstration of what committee
governance is good at (a large, coherent, multi-vendor standard shipping on schedule) and
what it is bad at (deciding a contested safety strategy quickly).

**Whatever the model, you need**: a public proposal process with a written record, a
stability policy stated *before* you need it, a deprecation policy, and a security-response
process.

### 14.4 Multiple implementations

**[CONTESTED]** A second implementation validates the specification, breaks vendor
lock-in, and expands platform reach — but doubles the conformance surface and creates
"which one is right?" ambiguity when the spec is incomplete.

**[VERSIONED] `gccrs` is the live experiment.** A GCC front end for Rust, motivated by
reaching every target GCC supports without depending on LLVM-based rustc. Its 2026 status
is a useful reality check on how long a second implementation takes: the project stated its
**2026 goal as being able to *mis*-compile the Linux kernel** — explicitly, an experimental
compiler that produces binaries that may not run correctly — with milestones ordered as
"embedded Rust compiler" → "Rust for Linux compiler" → "general-purpose compiler." As of
mid-2026 it handles simple standalone programs, having spent the first half of the year
finding and fixing problems in attribute handling, name resolution, and resource
management by testing against kernel crates. The project began in earnest around 2020.
**Budget five-plus years for a second implementation of a non-trivial language, and note
that gccrs deliberately targets Rust 1.49 semantics rather than chasing current Rust.**
