---
name: language-design-parsing-and-types
description: "Use when designing a language or building a compiler front end: the questions that determine everything else, the design principles that hold up, syntax; lexing, parsing approaches (recursive descent, Pratt, LR, generators), error recovery, CST vs AST; name resolution and modules; and type systems — the design space, inference (Hindley–Milner, bidirectional), unification and the occurs check, traits, type classes, and interfaces, generics (monomorphize or erase), ownership, borrowing, and linearity, the other static analyses, compile-time execution and metaprogramming, and effects. Includes the router for the whole programming-language-development reference."
---

# Programming Language Development: Language Design, Lexing and Parsing, Names and Modules, and Type Systems

> **Part 1 of 5** of the *Programming Language Development* reference (plugin `programming-language-development`), covering §0–§4. Sibling skills: `language-irs-optimization-and-backends` (§5–§7), `language-runtimes-interpreters-and-jits` (§8–§9), `language-diagnostics-tooling-and-evolution` (§10–§14), `language-development-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §0. Routing

### 0.1 The pipeline

```
SOURCE TEXT
  │  LEXER ─────────── tokens (+ trivia, spans)                            §2
  │  PARSER ────────── CST/AST (+ error recovery)                          §2
  ▼
FRONT END
  │  NAME RESOLUTION ─ bind identifiers to declarations; modules, scopes   §3
  │  TYPE CHECKING ─── inference, coercion, trait/class resolution         §4
  │  SEMANTIC ANALYSIS ─ borrow/effect/exhaustiveness/definite-assignment  §4.7
  ▼
MIDDLE END
  │  LOWER to IR ───── SSA / CPS / ANF; desugar; monomorphize              §5
  │  OPTIMIZE ──────── inline, constant-fold, DCE, GVN, LICM, vectorize    §6
  ▼
BACK END
  │  INSTRUCTION SELECTION ─ IR → target instructions                      §7
  │  REGISTER ALLOCATION ─── virtual → physical registers                  §7.3
  │  SCHEDULING / EMISSION ─ object code, debug info                       §7
  ▼
RUNTIME + LINK ───── GC, scheduler, FFI, unwinding, dynamic loading        §8
```

**[DURABLE] The two most consequential structural decisions are made before you write a
line of the pipeline:**
1. **What is your IR, and how many do you have?** (§5 → `language-irs-optimization-and-backends`) Every serious compiler ends up with
   at least three levels. Deciding this late means rewriting everything.
2. **Is the front end reusable by an IDE?** (§11 → `language-diagnostics-tooling-and-evolution`) A compiler designed as a batch
   source-to-binary pipeline cannot be turned into a responsive language server without
   substantial rearchitecture. Design for incrementality from day one or accept that you
   will do it twice.

### 0.2 The question router

| Asked about... | Go to |
|---|---|
| Should this be a language at all? Design philosophy, trade-offs | §1 |
| Lexing, parsing, grammars, error recovery, syntax design | §2 |
| Scopes, modules, imports, name resolution | §3 |
| Type systems, inference, generics, traits, effects, ownership | §4 |
| IR design — SSA, CPS, ANF, MLIR, lowering | §5 → `language-irs-optimization-and-backends` |
| Optimization passes and where they belong | §6 → `language-irs-optimization-and-backends` |
| Code generation, instruction selection, register allocation, backends | §7 → `language-irs-optimization-and-backends` |
| Runtime: memory management, GC, concurrency, FFI, exceptions | §8 → `language-runtimes-interpreters-and-jits` |
| Interpreters, bytecode VMs, JIT | §9 → `language-runtimes-interpreters-and-jits` |
| Error messages and diagnostics | §10 → `language-diagnostics-tooling-and-evolution` |
| Incremental compilation, IDE, LSP | §11 → `language-diagnostics-tooling-and-evolution` |
| Testing, fuzzing, formal verification | §12 → `language-diagnostics-tooling-and-evolution` |
| Standard library, ecosystem, tooling | §13 → `language-diagnostics-tooling-and-evolution` |
| Evolution, versioning, governance, deprecation | §14 → `language-diagnostics-tooling-and-evolution` |
| "Don't do this" | §15 → `language-development-reference` |
| "Which approach is better?" | §16 → `language-development-reference` (contested) |
| "Is this still current?" | §17 → `language-development-reference` |
| Books, papers, people | §18 → `language-development-reference` |

---

## §1. Language Design

### 1.1 The questions that determine everything else

Answer these before implementation; each one propagates through the whole pipeline.

| Question | Options | Downstream consequences |
|---|---|---|
| **Static or dynamic typing?** | Static, dynamic, gradual | Determines whether the type checker is a phase or a runtime |
| **Memory management?** | Manual, RAII/ownership, refcount, tracing GC, region/arena | The single largest runtime-design driver (§8.1 → `language-runtimes-interpreters-and-jits`) |
| **Compiled or interpreted?** | AOT, JIT, bytecode VM, tree-walk, transpile | Determines the whole back end |
| **Generics: monomorphize or erase?** | Monomorphize (C++, Rust), erase (Java, Go pre-1.18), dictionary-pass (Haskell, Swift) | Code size vs. compile time vs. runtime cost (§4.5) |
| **Concurrency model?** | Threads+locks, async/await, actors, CSP, STM, structured concurrency | Colours your entire function type system (§8.3 → `language-runtimes-interpreters-and-jits`) |
| **Mutability default?** | Mutable, immutable, controlled | Affects optimization opportunity enormously |
| **Nullability?** | Nullable-by-default, option types, non-null-by-default | Tony Hoare's "billion-dollar mistake." Option types are the settled answer for new languages |
| **Error handling?** | Exceptions, result types, error returns, panics | Interacts with every ABI and FFI decision (§8.4 → `language-runtimes-interpreters-and-jits`) |
| **Metaprogramming?** | None, macros (hygienic or not), reflection, compile-time execution, templates | Determines whether your compiler is also an interpreter (§4.8) |

### 1.2 The design principles that hold up

- **[DURABLE] Simplicity is a budget, not a virtue.** You get a fixed complexity budget;
  every feature spends it. The question is never "is this feature good?" but "is this
  feature worth what it costs in interaction with everything else?" Feature *interactions*
  are superlinear, which is why languages get harder to learn faster than they get bigger.
- **Orthogonality**: features should compose without special cases. Every special case is
  a thing to learn, a thing to implement, and a source of bugs at the seams.
- **The principle of least astonishment** applies to *the population you're targeting*, not
  to language theorists.
- **Make the right thing easy and the wrong thing hard.** Rust's success is mostly this
  principle applied to memory.
- **Errors should be impossible, then caught at compile time, then caught at runtime, then
  documented — in that order of preference.**
- **[CONTESTED] "Worse is Better" (Richard Gabriel, 1989)** — the New Jersey school
  (simplicity of *implementation* beats completeness; ship it) versus the MIT/Stanford
  school (correctness and completeness first). C and Unix won with the first; the second
  produced better artifacts that fewer people used. This tension is unresolved and shows
  up in every language committee.
- **Hyrum's Law**: with enough users, every observable behaviour of your implementation
  becomes a promise, whether or not you specified it. **Specify aggressively, and
  deliberately randomize what you refuse to promise** (Go randomizes map iteration order
  precisely to prevent people depending on it — a technique worth stealing).

### 1.3 Syntax

**[DURABLE] Syntax is the least important part of a language and the part people argue
about most.** That said, it is the interface, and interfaces matter:
- **Familiarity has enormous value.** Jakob's Law applies to languages: users arrive with
  expectations from every other language they know. Novel syntax is a tax paid on every
  reader forever, and it should buy something real.
- **Readability > writability.** Code is read far more than written. Perl and APL optimized
  the wrong one.
- **Prefer unambiguous grammars.** If your grammar needs unbounded lookahead or a "lexer
  hack," your tooling — formatters, highlighters, IDEs, other implementations — will
  suffer forever. C's `(a)*b` ambiguity (cast or multiply? depends on whether `a` is a
  type) is the canonical example.
- **Design for tooling from the start**: a formatter, a syntax highlighter, and an IDE all
  want a *lossless* CST with trivia preserved (§2.4).

> **⚠️ GOTCHA — significant whitespace and tabs.** If you choose indentation-sensitive
> syntax, you must specify the tab/space interaction exactly, at the lexer level, in
> version one. Python took until Python 3 to make mixing an error, and it caused real bugs
> for a decade.

> **⚠️ GOTCHA — reserve keywords generously.** Adding a keyword later breaks every program
> using it as an identifier. Languages handle this with contextual keywords (complexity),
> editions (Rust — §14.2 → `language-diagnostics-tooling-and-evolution`), or just breaking people. Reserve more than you need on day one.

---

## §2. Lexing and Parsing

### 2.1 Lexing

Convert characters to tokens. The parts people underestimate:
- **Unicode.** Identifiers (UAX #31), normalization (NFC — decide and enforce it, or `é`
  and `é` are different identifiers), and **bidirectional-override characters, which are a
  security issue**: the "Trojan Source" attack uses them to make source read differently
  to a human than to the compiler. Reject or warn on bidi control characters in source.
- **Spans/locations on every token.** Byte offsets plus a line-index side table is the
  standard efficient design — computing line/column lazily from a precomputed line table
  beats tracking it per character.
- **Trivia** (whitespace, comments) — either preserve them attached to tokens or you cannot
  build a formatter or a lossless refactoring tool later (§2.4).
- **Interpolated strings, raw strings, and nested comments** are where hand-written lexers
  earn their keep; regex-based lexer generators struggle with them.

### 2.2 Parsing — choosing an approach

| Approach | Notes |
|---|---|
| **Recursive descent + Pratt** | **The overwhelming choice of production compilers** (GCC, Clang, rustc, Go, TypeScript, V8). Hand-written, readable, arbitrary lookahead, and — decisively — *excellent error recovery and error messages* |
| LL(k) generators (ANTLR) | Good tooling, good for DSLs; less control over errors |
| LALR generators (yacc/bison) | Compact, fast; conflicts are famously painful to debug; poor error messages |
| GLR / Earley | Handle ambiguous grammars; slower; useful for language *research* and for parsing C++ |
| PEG / packrat | Unambiguous by construction (ordered choice), linear with memoization; **ordered choice silently hides ambiguity, which is a footgun** |
| Combinators | Elegant, great for prototypes; error messages and performance need work |

**[DURABLE] Essentially every widely-used production compiler uses hand-written recursive
descent, and the reason is error recovery.** A generated parser gives up or produces a
generic message; a hand-written one can say "you forgot a semicolon here" and continue.
Since the parser's output feeds an IDE that sees broken code 100% of the time, this is not
a minor consideration.

**Pratt parsing (top-down operator precedence)** is the right technique for expressions:
each token gets a binding power, and precedence and associativity fall out of comparing
them. It's about 50 lines and handles prefix, infix, postfix, and mixfix cleanly.

### 2.3 Error recovery

**[DURABLE] The parser's job is not to reject bad programs. It is to produce a usable tree
from bad programs**, because that is the input it receives most of the time.
- **Error nodes / poison nodes**: represent "something was here but it was wrong" in the
  tree so later phases can continue and produce *their* errors too.
- **Panic-mode recovery with synchronization tokens**: on error, skip to the next `;`, `}`,
  or start-of-declaration and resume.
- **Insertion/deletion repair**: hypothesize a missing token and continue.
- **Never cascade.** One missing brace producing 400 errors is the classic failure. Suppress
  errors within a short distance of a previous one, and suppress errors *derived from*
  poison nodes.

### 2.4 CST vs. AST

- **CST (concrete syntax tree)**: every token, every space, every comment. Required for
  formatters, refactoring tools, and IDEs. Rust-analyzer's **rowan** and the
  **Roslyn** "red-green tree" design are the reference implementations: a persistent,
  immutable "green" tree of shared nodes plus a lightweight "red" layer providing parent
  pointers and absolute positions.
- **AST**: semantic structure, trivia discarded.
- **[DURABLE] Build the CST and derive the AST from it.** Going the other direction is
  impossible. This is the single most common regret in compiler front-end design, because
  the IDE requirement always arrives later than the compiler requirement.

---

## §3. Names, Scopes, and Modules

### 3.1 Name resolution

Bind every identifier to a declaration. Sounds simple; is not.
- **Scoping**: lexical (almost always correct) vs. dynamic (almost always a mistake).
- **Shadowing**: allowed, warned, or forbidden. Rust allows and uses it heavily; many
  languages warn.
- **Forward references**: can a function call something declared later? At top level,
  usually yes (requiring a separate declaration-collection pass); inside a block, usually
  no. **This decision determines whether name resolution is one pass or two.**
- **Namespaces**: are types, values, macros, and labels in the same namespace? (C has
  separate struct/ordinary namespaces; Rust separates types and values; Lisp-2 vs. Lisp-1
  is the oldest version of this argument.)
- **Overloading** multiplies resolution complexity by type checking — now name resolution
  and type checking are mutually dependent, and you may need to interleave them.

### 3.2 Modules

**[DURABLE] Module systems are where languages accrete the most regret**, because module
semantics touch compilation units, linking, versioning, packaging, and the file system all
at once. The decisions:

| Decision | Options |
|---|---|
| Unit of modularity | File, directory, explicit declaration, package |
| Import granularity | Whole module, selected names, glob |
| Visibility | Public/private, `pub(crate)`-style graded, explicit export lists |
| Cyclic imports | Allowed (complicates compilation order), forbidden (simplifies everything) |
| Name-to-file mapping | Implicit (Java, Python) or explicit (Rust `mod`, C++ modules) |
| Separate compilation | Per-file, per-module, per-package, whole-program |

**[DURABLE] Forbid cyclic module dependencies if you possibly can.** They force
whole-program analysis, complicate incremental compilation, and are almost always a design
smell in user code. Go forbids them; the ecosystem is measurably healthier for it.

> **⚠️ GOTCHA — C++ modules are the cautionary tale.** Standardized in C++20; **GCC 16.1
> (April 2026) still describes its C++20 modules support as experimental, requiring
> `-fmodules`.** Six years from standardization to "still experimental" in a major
> implementation is what happens when a module system must interoperate with a
> textual-inclusion legacy. **Design modules before you have a legacy, not after.**

---

## §4. Type Systems

### 4.1 The design space

| Axis | Options |
|---|---|
| Checked when | Static, dynamic, gradual, optional |
| Inference | None, local, bidirectional, global (HM) |
| Polymorphism | Parametric (generics), ad-hoc (overloading/traits), subtype, row |
| Subtyping | None, nominal, structural, both |
| Variance | Invariant, co/contravariant, declaration-site or use-site |
| Higher-kinded | No, yes (Haskell, Scala) |
| Dependent | No, limited (const generics, refinement), full (Idris, Lean, Agda) |
| Effects | Implicit, checked exceptions, monadic, algebraic effect handlers |
| Linearity | None, affine (Rust ownership), linear, uniqueness |

### 4.2 Inference

**Hindley–Milner (Algorithm W)** — full inference for the let-polymorphic lambda calculus.
Unification-based, principal types, and no annotations required anywhere. The catch:
**HM does not survive contact with subtyping, higher-rank types, or type classes without
significant extension**, and its error messages are notoriously bad — unification fails at
some arbitrary point far from the actual mistake.

**Bidirectional type checking** — the modern default. Split into two mutually recursive
judgments: *checking* (`Γ ⊢ e ⇐ T`, "does `e` have type `T`?") and *synthesis*
(`Γ ⊢ e ⇒ T`, "what type does `e` have?"). Annotations at the boundaries.
- **Why it won**: it scales to subtyping, higher-rank polymorphism, dependent types, and
  GADTs, where HM does not; it needs fewer annotations than you'd think; and — the reason
  practitioners care — **error messages are dramatically better**, because when checking
  fails you know the *expected* type and can report both sides.
- Used in some form by Rust, Swift, TypeScript, Scala 3, Agda, Idris.

**Local type inference** (C#, Java, Go, C++ `auto`) — infer variable types from
initializers and generic instantiations from arguments; require annotations on function
signatures. **[DURABLE] Requiring signature annotations is a feature, not a limitation**:
it makes the code self-documenting, keeps errors local, makes separate compilation
tractable, and makes the IDE's job possible.

> **⚠️ GOTCHA — global inference and error locality are in direct tension.** With full
> inference, an error in one function can surface as a type error in an unrelated one.
> Every language with global inference eventually adds a "please annotate your top-level
> definitions" lint. Consider just requiring them.

### 4.3 Unification and the occurs check

```
unify(a, b):
  a, b = resolve(a), resolve(b)          # follow substitutions (union-find)
  match (a, b):
    (Var x, Var y) if x == y  -> ok
    (Var x, t) | (t, Var x)   -> occurs_check(x, t); bind(x, t)   ← DON'T SKIP THIS
    (Con(c1, as), Con(c2, bs)) if c1 == c2 && len equal -> zip-unify
    _                          -> type error (report BOTH sides and the location)
```
**The occurs check** prevents binding `x := List<x>`, which creates an infinite type. Skip
it and your compiler hangs or stack-overflows on a program like `let f = fun x -> x x`.
Use **union-find with path compression** for the substitution or unification is
accidentally quadratic.

**Levels/ranks for generalization**: the naive "generalize all free variables not in the
environment" is O(n) in environment size at every `let`. The standard fix is Rémy's
level-based generalization — tag each type variable with the `let`-depth at which it was
created and generalize only those deeper than the current level. Every efficient HM
implementation does this.

### 4.4 Traits, type classes, and interfaces

The mechanism for ad-hoc polymorphism, and it comes in three flavours:
- **Nominal interfaces** (Java, C#): a type explicitly declares it implements an interface.
  Simple, but you cannot retrofit an interface onto a type you don't own.
- **Structural** (Go, TypeScript): if it has the methods, it satisfies the interface. Fixes
  retrofitting; loses the ability to distinguish two interfaces with the same shape and
  different meaning.
- **Type classes / traits** (Haskell, Rust, Swift): implementations are declared
  *separately* from both the type and the interface. Solves retrofitting *and* keeps
  nominality — at the cost of needing **coherence** rules.

**Coherence and the orphan rule.** If two crates can both implement `Trait` for `Type`,
which one applies? Incoherence breaks type-directed dispatch and can break soundness.
Haskell and Rust enforce coherence via the **orphan rule**: you may implement a trait for
a type only if you own the trait or the type. It is the single most-complained-about rule
in Rust and it is load-bearing.

**Implementation strategies**: dictionary passing (pass a vtable of the implementation —
Haskell, Swift), monomorphization (generate a specialized copy — Rust static dispatch), or
vtables at runtime (`dyn Trait`, Go interfaces).

**⚠️ Trait resolution is a solver, and solvers have performance and termination problems.**
Rust's trait system is expressive enough that resolution can loop or blow up exponentially.
**[VERSIONED]** rustc has been building a **next-generation trait solver** for years
precisely to fix long-standing soundness bugs, unblock features (implied bounds, negative
impls), and improve compile times; it reached production use in coherence checking and, as
of 2026, stabilization work continues alongside **Polonius** (the next-generation borrow
checker). The lesson for a language designer: **an expressive trait/instance-resolution
system is a Prolog interpreter in your compiler. Budget accordingly.**

### 4.5 Generics: monomorphize or erase?

**[CONTESTED, and one of the genuinely load-bearing decisions.]**

| | **Monomorphization** (C++, Rust) | **Erasure / dictionaries** (Java, Haskell, Swift) |
|---|---|---|
| Runtime cost | **Zero** — specialized code, inlinable | Indirection: boxing, vtables, dictionaries |
| Code size | **Explodes** — one copy per instantiation | One copy |
| Compile time | **Slow** — the dominant cost in large Rust and C++ builds | Fast |
| Separate compilation | Hard — need the generic body available | Clean |
| Reflection on type args | Available | Erased (Java's `List<T>` doesn't know `T` at runtime) |
| Error messages | Instantiation-time errors, often terrible (C++ templates pre-concepts) | Declaration-time errors |

Go's 1.18 generics chose a **middle path (GC shape stenciling)**: monomorphize by
*representation class* rather than by exact type, so all pointer-shaped types share one
instantiation. This bounds code growth while keeping most of the performance.

**[DURABLE] Whichever you choose, define errors at the *declaration* site.** C++ templates
famously deferred all checking to instantiation, producing the pathological error messages
that concepts (C++20) exist to fix. Rust's trait bounds check the generic body against its
bounds up front. This is worth real implementation effort.

### 4.6 Ownership, borrowing, and linearity

Rust's contribution is proving that **affine types plus region inference can eliminate
memory-safety bugs at compile time with no runtime cost**, in a language people actually
ship. The machinery:
- **Ownership**: each value has one owner; drop at scope end (RAII).
- **Borrowing**: `&T` (shared, many) / `&mut T` (unique, one). The XOR rule — aliasing xor
  mutation — is what makes the whole thing sound *and* is what makes it hard to learn.
- **Lifetimes**: regions inferred by the borrow checker; annotations only where inference
  can't decide.

**[VERSIONED] NLL (non-lexical lifetimes) shipped in 2018; Polonius** is the next-generation
formulation, designed to accept currently-rejected patterns (notably "lending iterators").
Rust's own 2026 project-goal updates describe an "alpha" Polonius being tested on CI
alongside the next-gen trait solver, with worst-case slowdowns still being tracked. **The
honest read: borrow checking is a research area with a shipped product on top of it, and
the shipped product's rules are still being refined eight years in.**

**Alternatives worth knowing**: linear types (must use exactly once — Linear Haskell),
uniqueness types (Clean), region/arena inference (MLKit, Cyclone — the direct ancestor of
Rust's design), and Swift's ARC with `~Copyable`/borrowing annotations retrofitted.

### 4.7 The other static analyses

These aren't "type checking" but live in the same phase and are equally load-bearing:
- **Exhaustiveness checking for pattern matching.** [DURABLE] **This is one of the highest
  value-per-implementation-effort features in language design.** Maranget's algorithm
  ("Warnings for pattern matching," 2007) is the standard reference and is genuinely
  implementable in a few hundred lines. It converts a whole class of runtime bugs into
  compile errors and it is what makes sum types pleasant instead of tedious.
- **Definite assignment** — is this variable initialized on every path?
- **Reachability / dead code**, **unused variables and imports**.
- **Effect checking** (§4.9).

### 4.8 Compile-time execution and metaprogramming

The spectrum, in increasing order of power and danger:
1. **Constant folding** — the compiler evaluates `2+2`.
2. **`constexpr`/`comptime`** — arbitrary evaluation at compile time (C++, **Zig's
   `comptime`**, which is also how Zig does generics).
3. **Hygienic macros** — syntax-to-syntax transforms that respect scope (Scheme, Rust).
4. **Procedural macros / compiler plugins** — arbitrary code running in the compiler.
5. **Full reflection** — programs inspecting and generating themselves.

**[VERSIONED, and a genuinely big deal] C++26 shipped static reflection**, which Herb
Sutter called "the biggest upgrade since templates" and "C++'s decade-defining rocket
engine." **The ISO committee completed technical work on C++26 on 28 March 2026** in
London; the headline features are **static reflection, contracts, `std::execution`
(sender/receiver), and a hardened standard library**. **GCC 16.1 (30 April 2026) already
ships reflection and contracts.** Note the syntax churn as a lesson: the reflection
operator changed from `^` to `^^` during standardization, so early adopter code needed
migration.

> **⚠️ GOTCHA — compile-time execution means your compiler contains an interpreter, and
> that interpreter is a security boundary and a performance cliff.** You need: a step
> limit (or programs won't terminate), determinism (or builds aren't reproducible), a
> decision about whether it can do I/O (**it should not**), and an answer for what it means
> to debug it. Zig's community discussions consistently name `comptime` as both its best
> feature and a significant pain point — that's the shape of this trade-off.

### 4.9 Effects

An active research frontier that is reaching production:
- **Checked exceptions** (Java) — the first mainstream effect system, and widely considered
  a partial failure because it lacked polymorphism: you couldn't write a higher-order
  function generic over what its argument throws.
- **Monadic effects** (Haskell) — expressive, composes badly (monad transformers).
- **Algebraic effects and handlers** (Koka, Eff, OCaml 5's effect handlers) — the current
  best answer. Effects are operations; handlers interpret them. This is what makes OCaml 5's
  concurrency work without colouring functions.
- **Function colouring** (§8.3 → `language-runtimes-interpreters-and-jits`): async/await is an *ad-hoc, unprincipled effect system*.
  This is the strongest argument for doing effects properly.
