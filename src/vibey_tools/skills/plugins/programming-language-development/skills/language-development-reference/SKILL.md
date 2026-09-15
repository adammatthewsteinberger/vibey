---
name: language-development-reference
description: "Use when reviewing a language or compiler design for known anti-patterns, weighing contested questions (static vs dynamic typing, monomorphization vs erasure, GC vs ownership, async/await vs green threads, LLVM or not, Safe C++ vs Profiles, sea of nodes, batteries-included standard library, formal verification's cost/benefit, how much syntax novelty), checking whether a toolchain or language-version claim is still current (snapshot verified August 2026), finding the books, papers, and primary sources, or needing the build-it-in-order checklist, numbers, and compiler-bug triage. Companion to the other programming-language-development skills."
---

# Programming Language Development: Anti-Patterns, Contested Questions, Currency, and Canon

> **Part 5 of 5** of the *Programming Language Development* reference (plugin `programming-language-development`), covering §15–§20. Sibling skills: `language-design-parsing-and-types` (§0–§4), `language-irs-optimization-and-backends` (§5–§7), `language-runtimes-interpreters-and-jits` (§8–§9), `language-diagnostics-tooling-and-evolution` (§10–§14). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §17 below for the currency snapshot and what goes stale first.

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

## §15. Anti-Patterns

| Anti-pattern | Why | Instead |
|---|---|---|
| AST-only front end, no CST | Formatters, refactoring, and IDEs become impossible | Lossless CST, derive the AST (§2.4 → `language-design-parsing-and-types`) |
| Parser that gives up on the first error | The IDE sees broken code 100% of the time | Error nodes + recovery (§2.3 → `language-design-parsing-and-types`) |
| Generated parser for a production language | Poor error messages, poor recovery | Hand-written recursive descent + Pratt |
| One IR for everything | Every pass handles every abstraction level | 3+ levels, progressive lowering (§5.1 → `language-irs-optimization-and-backends`) |
| No IR verifier | Miscompiles found by users, not CI | Verifier after every pass in debug builds |
| No textual IR round-trip | Undebuggable, untestable passes | Print/parse your IR |
| Dropping spans during lowering | Debug info and diagnostics silently degrade | Carry spans to the end (§10.4 → `language-diagnostics-tooling-and-evolution`) |
| Skipping the occurs check | Compiler hangs on `fun x -> x x` | Do the occurs check (§4.3 → `language-design-parsing-and-types`) |
| Naive HM generalization | Accidentally quadratic in environment size | Levels/ranks (§4.3 → `language-design-parsing-and-types`) |
| Global type inference, no signature annotations | Errors surface far from the cause | Require signatures; infer bodies |
| Deferring generic errors to instantiation | Pre-concepts C++ template errors | Check the generic body against its bounds |
| Undefined behaviour for convenience | The most hostile compiler behaviour there is | Define it — even "unspecified" beats "undefined" (§6.2 → `language-irs-optimization-and-backends`) |
| Cascading errors | One typo, 400 messages | Suppress derived errors (§2.3 → `language-design-parsing-and-types`) |
| Warnings everyone ignores | Trains users to ignore all output | Small high-precision default set (§10.3 → `language-diagnostics-tooling-and-evolution`) |
| Compile-time execution with I/O or no step limit | Non-reproducible builds, non-terminating compiles | Sandbox and bound it (§4.8 → `language-design-parsing-and-types`) |
| Cyclic module dependencies allowed | Forces whole-program analysis, kills incrementality | Forbid them (§3.2 → `language-design-parsing-and-types`) |
| Phase-ordered batch compiler, LSP added later | The largest refactor a compiler team can do | Query-based from day one (§11.2 → `language-diagnostics-tooling-and-evolution`) |
| Two implementations, one for the compiler and one for the IDE | Guaranteed divergent behaviour | One engine, two entry points |
| Optimizing before you have benchmarks | You will optimize the wrong pass | Measure first (§6.2 → `language-irs-optimization-and-backends`) |
| Adding a keyword without an edition mechanism | Breaks every program using it as an identifier | Reserve early or ship editions (§14.2 → `language-diagnostics-tooling-and-evolution`) |
| Inventing your own ABI while wanting C FFI | Interop bugs on every platform corner | Implement the platform ABI exactly (§7.4 → `language-irs-optimization-and-backends`) |
| Letting panics/exceptions unwind into C | UB | Catch at the boundary (§8.4 → `language-runtimes-interpreters-and-jits`) |
| Choosing GC late | Constrains calling convention, optimizer, FFI | Decide before the back end (§8.1 → `language-runtimes-interpreters-and-jits`) |
| No formatter, or a formatter with options | Permanent style arguments | Ship one, with no options (§13 → `language-diagnostics-tooling-and-evolution`) |
| No fuzzing on an optimizer | Miscompiles reach users | Csmith/YARPGen-style fuzzing in CI (§12.1 → `language-diagnostics-tooling-and-evolution`) |
| Untested diagnostics | They rot immediately | Snapshot-test error output (§10.2 → `language-diagnostics-tooling-and-evolution`) |

---

## §16. Contested Questions

**16.1 Static vs. dynamic typing.** The empirical literature is genuinely weaker than
advocates on both sides claim — controlled studies are small, short, and use toy tasks.
What is well-supported: static types help *at scale*, on *large teams*, over *long
maintenance periods*, and enable tooling (completion, refactoring) that dynamic languages
approximate at best. Gradual typing (TypeScript, mypy, Sorbet) is the market's revealed
preference, which is itself informative.

**16.2 Monomorphization vs. erasure.** §4.5 → `language-design-parsing-and-types`. Runtime speed vs. compile time and code size.

**16.3 GC vs. ownership.** Rust proved ownership is viable in a mainstream language; it also
proved it has a real learning-curve cost. GC is easier to use and rules out whole domains
(hard real-time, kernel, tiny embedded). Neither wins; the domain decides.

**16.4 async/await vs. green threads.** §8.3 → `language-runtimes-interpreters-and-jits`. Function colouring vs. runtime requirement.

**16.5 LLVM or not.** §7.1 → `language-irs-optimization-and-backends`. Best-in-class codegen and target coverage vs. compile speed,
dependency weight, and API churn. Zig is running the "not" experiment in public; rustc is
running the "both" experiment. Note that Cranelift's ~20% codegen speedup yields only ~5%
total build speedup in rustc — **the backend is often not the bottleneck people assume**.

**16.6 Safe C++ vs. Profiles.** WG21 rejected borrow checking for C++ and chose the
Profiles direction; the enforcement attribute then slipped to C++29. *For Profiles*:
incremental, no rewrite, works on existing code. *Against*: many practitioners consider it
unable to deliver the guarantees borrow checking does. **C++26 did ship real safety
improvements you get by recompiling** — hardened standard library plus contracts — so this
is not nothing; whether it's sufficient is exactly the disputed point.

**16.7 Sea of nodes.** Powerful reordering vs. debuggability. V8 moving parts of TurboFan
away from it is evidence that the debuggability cost is real at scale.

**16.8 Batteries-included standard library.** §13 → `language-diagnostics-tooling-and-evolution`.

**16.9 Formal verification's cost/benefit.** CompCert's Csmith result is the strongest
pro-verification evidence in the field; the counter is that CompCert optimizes less and
took enormous effort. Translation validation (Alive2) is the compromise most projects
should actually adopt.

**16.10 How much syntax novelty is justified?** §1.3 → `language-design-parsing-and-types`. Familiarity is worth a great deal;
occasionally a genuinely better notation (Rust's `?`, pattern matching, pipelines) earns
its cost. The failure mode is novelty *for its own sake*.

---

## §17. Currency Snapshot — verified August 2026

| Thing | Status as of Aug 2026 | Decay risk |
|---|---|---|
| **LLVM** | **22.1.x** current (22.1.0 released 24 Feb 2026; 22.1.8 in June). ~6-month feature cadence. LLVM 22 adds Armv9.7-A and GICv5 assembly support, C2y work in Clang (named loops), full MLIR-to-LLVM-IR translation for OpenMP TASKLOOP, RISC-V tail folding by default, ThinLTO distributed-build improvements | Medium |
| **MLIR** | Ships in the LLVM monorepo, moves with its releases; no separate qualification of the release branch. Substrate for Mojo, IREE, Triton, Flang | Medium |
| **GCC** | **16.1** released 30 April 2026. **C++20 by default**; ships **C++26 reflection and contracts** and safety hardening. ⚠️ **C++20 modules still experimental, requiring `-fmodules`** | Medium |
| **C++26** | ⚠️ **Done.** WG21 completed technical work **28 March 2026** (London Croydon; 210 experts, 24 nations); officially shipped by WG21 that date. Headline: **static reflection, contracts, `std::execution`, hardened stdlib**. Reflection operator changed `^` → `^^` during standardization. **`[[profiles::enforce]]` deferred to C++29**; Safe C++ borrow-checking proposal rejected. Herb Sutter stepped down as convener | Low |
| **WASI** | ⚠️ **WASI 0.3.0 released 11 June 2026.** Native async moved into the Component Model canonical ABI (`async func`, `stream<T>`, `future<T>`); **`wasi:io` removed entirely**. Wasmtime 45 ran the RC, Wasmtime 46 ships it; jco supports it. 0.2 remains supported/virtualizable. **Component Model 1.0 (formally specified) is the next milestone**; **WASI 1.0 planned, not shipped**. ⚠️ **Still no native multithreading.** Reporting on version status is inconsistent — check wasi.dev | **High** |
| **Zig** | **0.16 (beta) April 2026**; 0.17 in progress. Self-hosted **x86_64 backend default in Debug**; reported hello-world compile 22.8 s → 275 ms, self-build 75 s → 20 s. Release notes state the **x86 backend is now more robust than the LLVM backend** for implementing Zig. Open tracking issue to remove LLVM/LLD/Clang libraries entirely. 0.16 added Alpha/KVX/MicroBlaze/OpenRISC/PA-RISC/SuperH; **removed Solaris, AIX, z/OS** | **High** |
| **rustc backends** | LLVM production; **Cranelift** available via `rustup component add rustc-codegen-cranelift-preview` and `[profile.dev] codegen-backend = "cranelift"`. Measured ~**20% codegen-time reduction → ~5% total clean-build speedup** on Zed/Tauri/hickory-dns. GCC backend also maintained; all three behind `rustc_codegen_ssa` | Medium |
| **rustc type system** | **Next-gen trait solver** and **Polonius alpha**: both targeted for stabilization, with CI testing being expanded (compiler-team MCP, June 2026). Polonius worst case measured at ~60% slower than NLL on a pathological 5 KLOC function (42K loans, 255K statements, 125K outlives constraints) | **High** |
| **Cranelift** | 0.127.x (Dec 2025). Supports x86-64, aarch64, s390x, riscv64. Production use in Wasmtime | Medium |
| **gccrs** | ⚠️ **Still experimental.** Stated **2026 goal: be able to *mis*-compile the Linux kernel.** Handles simple standalone programs as of mid-2026; spent H1 2026 fixing attribute handling, name resolution, and resource management against kernel crates. Milestones: embedded → Rust-for-Linux → general purpose. Targets **Rust 1.49** semantics, not current Rust | Medium |
| **Mojo** | **1.0.0 beta1, 7 May 2026.** Chris Lattner / Modular; MLIR-based; Linux and macOS. **Language under the Modular Community License** (stdlib Apache-2.0-with-LLVM-exceptions) — *not* fully open source | **High** |
| **Carbon** | Experimental. Experimental **MVP 0.1 expected late 2026 at the earliest; production 1.0 after 2028** | Medium |

**Goes stale fastest:** WASI/Component Model versions; Zig's backend and LLVM-removal
progress; rustc's Polonius/next-solver status; Mojo. **Essentially never stale:** §1 → `language-design-parsing-and-types`
(design principles), §2 → `language-design-parsing-and-types` (parsing), §4.2 → `language-design-parsing-and-types`–4.3 (inference and unification), §5.2 → `language-irs-optimization-and-backends` (SSA),
§6.1 → `language-irs-optimization-and-backends` (the passes), §7.3 → `language-irs-optimization-and-backends` (register allocation), §9 → `language-runtimes-interpreters-and-jits` (interpreter ladder), §10 → `language-diagnostics-tooling-and-evolution` (diagnostics),
§15 (anti-patterns).

---

## §18. The Canon

### 18.1 Books

| Author | Work | Why |
|---|---|---|
| **Robert Nystrom** | ***Crafting Interpreters*** | **Free online.** The best starting point in existence: a tree-walker and a bytecode VM, both complete, both explained. Start here, always |
| Aho, Lam, Sethi, Ullman | *Compilers: Principles, Techniques, and Tools* ("the Dragon Book") | The classic. Strong on parsing theory, dated on modern back ends |
| **Appel** | ***Modern Compiler Implementation in ML/Java/C***; ***Compiling with Continuations*** | The best structured treatment of a full compiler; CwC is the CPS reference |
| **Muchnick** | *Advanced Compiler Design and Implementation* | The optimization reference. Dense, comprehensive, still the standard |
| **Cooper & Torczon** | *Engineering a Compiler* | The best modern textbook; better back-end coverage than the Dragon Book |
| **Pierce** | ***Types and Programming Languages*** (TAPL) | **The** type systems book. If you're designing a type system, this is not optional |
| Pierce (ed.) | *Advanced Topics in Types and Programming Languages* | The sequel: dependent types, subtyping, effects |
| **Harper** | *Practical Foundations for Programming Languages* | Rigorous, opinionated, structural |
| **Krishnamurthi** | *Programming Languages: Application and Interpretation* | **Free.** Excellent on design trade-offs |
| **Friedman & Wand** | *Essentials of Programming Languages* | Interpreters as the lens for understanding semantics |
| **Jones, Hosking, Moss** | ***The Garbage Collection Handbook*** | The GC reference, full stop |
| Smith & Nair | *Virtual Machines* | VM and JIT architecture |
| **Wirth** | *Compiler Construction* | Short, clear, complete. A single-sitting read |
| Grune et al. | *Parsing Techniques* | Exhaustive on parsing |

### 18.2 Papers worth reading directly

- **Cytron et al. (1991)**, "Efficiently Computing Static Single Assignment Form" — the
  classic SSA construction.
- **Braun et al. (2013)**, "Simple and Efficient Construction of SSA Form" — **use this one**.
- **Appel (1998)**, "SSA is Functional Programming" — the unifying insight.
- **Maranget (2007)**, "Warnings for Pattern Matching" — exhaustiveness checking.
- **Dunfield & Krishnaswami**, "Bidirectional Typing" (survey) — the modern inference guide.
- **Damas & Milner (1982)** — Algorithm W.
- **Chaitin (1981)** — register allocation as graph colouring; **Poletto & Sarkar (1999)** —
  linear scan; **Hack et al.** — SSA-based allocation and chordality.
- **Yang, Chen, Eide, Regehr (2011)**, "Finding and Understanding Bugs in C Compilers" —
  the Csmith paper, and the empirical case for verification.
- **Leroy**, the CompCert papers.
- **Thompson (1984)**, "Reflections on Trusting Trust."
- **Gabriel (1989)**, "Worse is Better."
- **Plotkin & Pretnar**, algebraic effects and handlers; **Leijen** on Koka.
- **Grossman et al.**, Cyclone (regions) — the direct ancestor of Rust's ownership model.

### 18.3 Primary sources and ongoing

- **LLVM**: `llvm.org/docs` (the Language Reference and Kaleidoscope tutorial), the
  discourse forums, `mlir.llvm.org`. **`rustc-dev-guide.rust-lang.org`** is arguably the
  best publicly-written description of a production compiler's architecture.
- **Cranelift** (`cranelift.dev`), **Wasmtime**, **Bytecode Alliance** blog,
  **`wasi.dev`**, the **Component Model book**.
- **Language design in public**: Rust RFCs and Inside Rust blog, Rust project goals,
  **Python PEPs**, **WG21 papers** (`open-std.org/jtc1/sc22/wg21`) and Herb Sutter's trip
  reports, Swift Evolution, Go proposals and the `research.swtch.com` design essays.
- **Zig devlog** (`ziglang.org/devlog`) — an unusually candid running account of compiler
  engineering decisions.
- **Conferences**: PLDI, POPL, OOPSLA, ICFP, CGO, SPLASH; the LLVM Developers' Meeting;
  Strange Loop's archive.
- **People to read**: Chris Lattner (LLVM, Swift, MLIR, Mojo), Graydon Hoare (Rust; his
  retrospective essays on language design are excellent), Andrew Kelley (Zig), Rich Hickey
  (design talks), Simon Peyton Jones (GHC, and the clearest explainer in the field),
  Niko Matsakis (Rust types), Russ Cox (Go), Anders Hejlsberg (Turbo Pascal, C#,
  TypeScript), Jonathan Corbet's LWN coverage of toolchain work.

---

## §19. Quick Reference

### 19.1 If you're building one, in order
1. **Read *Crafting Interpreters*.** Build a tree-walking interpreter. Ship it.
2. **Design the CST and spans before anything else** (§2.4 → `language-design-parsing-and-types`, §10.4 → `language-diagnostics-tooling-and-evolution`).
3. Hand-written recursive descent + Pratt, **with error recovery** (§2.2 → `language-design-parsing-and-types`–2.3).
4. Name resolution as a separate, queryable phase (§3.1 → `language-design-parsing-and-types`, §11.2 → `language-diagnostics-tooling-and-evolution`).
5. Type checker — **bidirectional** unless you have a reason (§4.2 → `language-design-parsing-and-types`).
6. **Exhaustiveness checking** — highest value per line of code you will write (§4.7 → `language-design-parsing-and-types`).
7. Bytecode VM, so you have a working language.
8. **A typed, verifiable, printable mid-level SSA IR** (§5 → `language-irs-optimization-and-backends`).
9. mem2reg/SROA + inlining + constant folding + DCE. Stop. Measure (§6.1 → `language-irs-optimization-and-backends`).
10. Backend: **LLVM for output quality, Cranelift/custom for speed** — and abstract over
    the choice from the start (§7.1 → `language-irs-optimization-and-backends`).
11. Diagnostics, snapshot-tested (§10 → `language-diagnostics-tooling-and-evolution`).
12. Language server, from the same engine (§11 → `language-diagnostics-tooling-and-evolution`).
13. Formatter, package manager, docs, debugger (§13 → `language-diagnostics-tooling-and-evolution`).

### 19.2 Numbers worth knowing
- Optimal register allocation is **NP-complete**; SSA interference graphs are **chordal**,
  so SSA-form allocation is polynomial.
- Interpreter ladder: bytecode ~**3–10×** over tree-walking; computed goto ~**1.5–2×** over
  switch; optimizing JIT **10–100×** over interpreter (§9.1 → `language-runtimes-interpreters-and-jits`).
- Cranelift in rustc: ~**20%** codegen-time reduction → ~**5%** total clean build.
- Zig self-hosted x86 backend: hello world **22.8 s → 275 ms**; self-build **75 s → 20 s**.
- Csmith found **hundreds** of bugs in GCC and LLVM and **zero** in CompCert's verified
  middle end.
- LLVM ships roughly **every 6 months**; GCC roughly **annually** (16.1: April 2026).

### 19.3 Compiler-bug triage
| Symptom | Look at |
|---|---|
| Wrong answer at `-O2`, right at `-O0` | **Miscompile.** Bisect passes (`opt-bisect-limit`), check UB in the source first |
| Compiler hangs | Occurs check, trait/instance resolution loop, unbounded comptime, pathological backtracking |
| Stack overflow in the compiler | Deep recursion on nested expressions — most compilers need an explicit depth limit or a manual stack |
| Wrong across an FFI boundary | ABI: struct classification, alignment, varargs, unwinding (§7.4 → `language-irs-optimization-and-backends`) |
| Works in debug, fails in release | UB, uninitialized memory, or an unsound optimization |
| Error message points at the wrong place | Span lost during lowering or desugaring (§10.4 → `language-diagnostics-tooling-and-evolution`) |
| IDE and compiler disagree | Two implementations, or a stale query cache (§11 → `language-diagnostics-tooling-and-evolution`) |

---

## §20. Sources and Method

**Method.** Narrative (not systematic) review. The durable material — §1 → `language-design-parsing-and-types` (design
principles), §2 → `language-design-parsing-and-types` (parsing), §4.2 → `language-design-parsing-and-types`–4.7 (type systems), §5.2 → `language-irs-optimization-and-backends` (SSA), §6 → `language-irs-optimization-and-backends` (optimization), §7.2 → `language-irs-optimization-and-backends`–7.4
(codegen), §8 → `language-runtimes-interpreters-and-jits` (runtimes), §9 → `language-runtimes-interpreters-and-jits` (interpreters and JITs), §10 → `language-diagnostics-tooling-and-evolution` (diagnostics), §12 → `language-diagnostics-tooling-and-evolution` (testing),
§15 (anti-patterns) — is synthesized from the primary literature and canonical texts in
§18. Every **time-sensitive** claim (toolchain versions, standard status, project state)
was verified against a primary or near-primary source in **August 2026** and is flagged in
§17 with a decay-risk rating. Where language designers genuinely disagree, §16 presents
both cases rather than adjudicating.

**Search log** (August 2026): LLVM current version and MLIR status · WebAssembly, WASI
Preview 3, and the Component Model · Zig's self-hosted backend and LLVM removal; Mojo and
Carbon status · rustc's Cranelift backend, Polonius, and the next-gen trait solver · C++26
finalization, contracts, reflection, and profiles · GCC 16 and gccrs.

**Primary and near-primary sources consulted (selected):**
- **LLVM Discussion Forums** release announcements (22.1.0 through 22.1.8); Arm's
  "What is new in LLVM 21/22" engineering blogs; **Phoronix** LLVM/Clang 22.1 coverage;
  `mlir.llvm.org` release notes
- **wasi.dev** — the WASI 0.3 release page and roadmap; **Bytecode Alliance** — "WASI 0.3
  Launched" and "The Road to Component Model 1.0"; the Component Model book
- **ziglang.org** — 0.16.0 release notes and the 2026 devlog; the ziglang/zig issue
  tracking LLVM/LLD/Clang removal; Ziggit and Lobsters discussion of the self-hosted x86
  backend default
- **Rust**: `rustc-dev-guide.rust-lang.org` (codegen backends, next-gen trait solving);
  the Rust Blog "Project goals update — April 2026"; rust-lang/compiler-team MCP #996 on
  CI-testing the next solver and Polonius alpha; the `rustc_codegen_cranelift` repo and
  the "Production-ready cranelift backend" project goal; **cranelift.dev**
- **Herb Sutter** — "C++26 is done! Trip report: March 2026 ISO C++ standards meeting";
  **InfoQ** and **isocpp.org** coverage of C++26 and GCC 16.1
- **gccrs** — the project's monthly reports (Dec 2025, Feb/Mar/May 2026), `rust-gcc.github.io`,
  **LWN.net** ("Progress toward compiling Linux with gccrs," "Gccrs after libcore")
- Canonical papers and books as listed in §18

**Confidence statement.** **High confidence** in §1–§13 → `language-design-parsing-and-types`, `language-diagnostics-tooling-and-evolution` and §15, §18–§19 — these rest on
the primary literature, canonical texts, and published compiler documentation. **High
confidence** in §17's verified items as of the stated date. **Moderate confidence** in the
performance figures quoted in §7.1 → `language-irs-optimization-and-backends` and §19.2: the Zig compile-time numbers come from
project announcements and community benchmarking rather than independent measurement, and
the Cranelift figures come from the Rust project's own measurements on three named
projects — both are directionally reliable and should not be treated as general
multipliers. The **WASI status in §7.5 → `language-irs-optimization-and-backends` is the least stable content in this document**: it
changed during 2026, and contemporaneous secondary sources describe 0.3 inconsistently as
released, in preview, and forthcoming — the dates given here follow wasi.dev and the
Bytecode Alliance directly, and should be re-checked rather than quoted from memory.
