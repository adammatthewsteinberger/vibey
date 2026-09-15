---
name: language-irs-optimization-and-backends
description: "Use when working on the middle or back end of a compiler. Covers why you need more than one IR, SSA, CPS/ANF and the other IR forms, MLIR as multi-level infrastructure, practical IR design rules, the optimization passes by category and the rules for writing them, where optimization happens, choosing a backend (LLVM, Cranelift, GCC, custom), instruction selection, register allocation (linear scan and its alternatives), the ABI, and WebAssembly as a target."
---

# Programming Language Development: Intermediate Representations, Optimization, and Code Generation

> **Part 2 of 5** of the *Programming Language Development* reference (plugin `programming-language-development`), covering §5–§7. Sibling skills: `language-design-parsing-and-types` (§0–§4), `language-runtimes-interpreters-and-jits` (§8–§9), `language-diagnostics-tooling-and-evolution` (§10–§14), `language-development-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §5. Intermediate Representations

### 5.1 Why more than one

**[DURABLE] Every serious compiler has at least three IR levels**, because the
transformations you want at each level need different information:
```
AST            source-shaped. Names, sugar, full spans. For type checking & diagnostics.
  ↓ desugar, resolve
HIGH IR        typed, desugared, still source-ish. For borrow checking, exhaustiveness,
               source-level optimizations.        (rustc: HIR → THIR)
  ↓ lower
MID IR         explicit control flow (CFG), explicit memory ops, SSA. THE optimization IR.
                                                 (rustc: MIR · Swift: SIL · Go: SSA · LLVM IR)
  ↓ lower
LOW IR         machine-shaped, target types, still virtual registers.  (LLVM MachineIR)
  ↓
MACHINE CODE
```
The rule of thumb: **lower when the information you're about to discard is no longer
needed, and no sooner.** Lowering too early loses the ability to give good errors and to
do high-level optimizations; lowering too late means every pass has to handle sugar.

### 5.2 SSA — Static Single Assignment

**[DURABLE] SSA is the dominant mid-level IR form and has been since the early 1990s.**
Every variable is assigned exactly once; control-flow merges use **φ (phi) functions**.

```
                      entry:
x = 1                   x₁ = 1
if c: x = 2             br c, then, join
y = x + 1             then:
                        x₂ = 2
                        br join
                      join:
                        x₃ = φ(x₁ from entry, x₂ from then)
                        y₁ = x₃ + 1
```
**Why it matters**: def-use chains are explicit and immediate, so constant propagation,
dead code elimination, GVN, and register allocation all become dramatically simpler. You
no longer need separate reaching-definitions analysis — SSA *is* that analysis, cached in
the IR.

**Construction**: the classic algorithm is Cytron et al. (1991) using **dominance
frontiers** to place φ-nodes. The modern practical alternative is **Braun et al. (2013),
"Simple and Efficient Construction of Static Single Assignment Form"** — builds SSA
directly during AST-to-IR translation without a separate dominance computation. **If you're
writing a compiler today, use Braun**; it is far simpler and produces comparable results.

**Destruction**: φ-nodes aren't real instructions. Converting out of SSA means inserting
copies on incoming edges, and doing it naively causes the **lost-copy** and **swap**
problems. Sreedhar et al.'s method is the standard correct approach. **This is where
subtle miscompiles live.**

### 5.3 The other IR forms

- **CPS (continuation-passing style)** — every call is a tail call; control flow is
  explicit as data. Elegant for functional languages, first-class control (call/cc), and
  compiler correctness proofs. Used by SML/NJ; the classic reference is Appel's
  *Compiling with Continuations*.
- **ANF (A-normal form)** — all intermediate results named, arguments are atomic. Roughly
  "CPS's benefits without the plumbing," and easier to read. Common in functional compilers.
- **Sea of nodes** — a graph where control and data dependencies are unified, allowing
  aggressive reordering. **HotSpot C2** and **V8's TurboFan** use it. Powerful, and
  notoriously hard to debug — V8 has been moving *away* from it in parts of the pipeline,
  which is worth knowing before you adopt it.
- **Stack-based bytecode** — JVM, CPython, WebAssembly. Compact, trivial to generate,
  slower to interpret than register-based.
- **Register-based bytecode** — Lua, Dalvik, LuaJIT. Fewer instructions dispatched;
  measurably faster interpretation.

**[DURABLE] CPS/ANF/SSA are the same thing viewed differently.** Appel's "SSA is Functional
Programming" (1998) is the paper that makes this click: an SSA φ-node is a function
parameter of a basic block, and a basic block is a continuation.

### 5.4 MLIR — multi-level IR as infrastructure

**[VERSIONED]** MLIR generalizes "have several IRs" into a framework: instead of one fixed
IR, you define **dialects** — extensible sets of operations, types, and attributes — and
write **progressive lowering** passes between them. A single module can hold operations
from several dialects at once.

Why it matters: it's the substrate for the ML-compiler ecosystem (TensorFlow, IREE, Triton),
for **Mojo** (Chris Lattner's language, explicitly built on MLIR), for Flang's OpenMP
lowering, and increasingly for hardware-adjacent domains. It ships inside the LLVM
monorepo, so it moves with LLVM's release train.

**When MLIR is right**: you have multiple abstraction levels, domain-specific optimizations,
heterogeneous targets (CPU/GPU/accelerator), or you want to reuse a large pass and
infrastructure ecosystem. **When it isn't**: a straightforward language targeting CPUs —
MLIR's conceptual overhead and build weight are substantial, and plain LLVM IR is a much
shorter path.

### 5.5 Practical IR design rules

1. **Make it verifiable and write the verifier first.** Run it after every pass in debug
   builds. This catches more miscompiles than any other single practice.
2. **Make it printable and parseable.** A textual round-trippable form makes every bug
   report, every test, and every debugging session tractable. LLVM's `.ll` format is the
   reason LLVM is debuggable at all.
3. **Explicit is better than implicit.** Make types, effects, and control flow explicit in
   the IR even when it's verbose.
4. **Preserve source locations through every transformation** or debug info and diagnostics
   degrade silently (§10.4 → `language-diagnostics-tooling-and-evolution`).
5. **Design for testability**: passes should be individually runnable on IR files.

---

## §6. Optimization

### 6.1 The passes, by category

| Category | Passes |
|---|---|
| **Local / peephole** | Constant folding, algebraic simplification, strength reduction, instruction combining |
| **Data-flow** | Constant propagation (SCCP), dead code elimination, common subexpression elimination, **GVN**, copy propagation |
| **Control-flow** | Branch folding, jump threading, block merging, tail duplication, **loop rotation** |
| **Loop** | LICM (loop-invariant code motion), unrolling, fusion/fission, interchange, strength reduction of induction variables, **vectorization** |
| **Interprocedural** | **Inlining** (the most important one), specialization, IPO/LTO, devirtualization, escape analysis |
| **Memory** | **SROA/mem2reg** (scalar replacement of aggregates — promoting memory to SSA registers), alias analysis, load/store forwarding |
| **Layout** | Basic-block placement, PGO-driven hot/cold splitting |

**[DURABLE] The 80/20 of optimization is inlining plus mem2reg/SROA plus constant folding
plus DCE.** Inlining exposes opportunities for everything else — it's a *meta*-optimization.
mem2reg turns naive stack-slot-per-variable codegen into real SSA, which is why a front end
can emit dumb, obviously-correct code and still get fast output.

### 6.2 The rules

1. **Correctness always beats speed.** A miscompile costs more than any optimization saves,
   and it destroys trust in the whole toolchain. Compiler bugs are the bugs users trust
   least and debug worst.
2. **Measure.** Optimizations interact non-obviously; your intuition about which passes
   matter will be wrong. Build the benchmark suite before the pass.
3. **Pass ordering matters and has no optimal solution** — the "phase-ordering problem."
   LLVM's pipeline is a hand-tuned sequence with several passes run more than once. Accept
   this; don't look for elegance here.
4. **Undefined behaviour is an optimization contract, and it is dangerous.** UB lets the
   optimizer assume things (no signed overflow, no null dereference, no strict-aliasing
   violation) and is the source of the most surprising and hostile compiler behaviour in C
   and C++. **If you're designing a new language, define the behaviour** — even "wraps" or
   "traps" or "unspecified but not undefined" is enormously better. Rust's decision to make
   overflow panic in debug and wrap in release is a defensible model.
5. **Debug builds must be fast to produce and debuggable.** `-O0` should be a genuinely
   different, minimal pipeline, not the same pipeline with fewer passes.

### 6.3 Where optimization happens

Modern systems do it at several levels, and it matters which:
- **Front end / high IR**: language-specific optimizations you can't express later
  (devirtualizing based on trait resolution, eliminating bounds checks using type
  information, monomorphization).
- **Mid-level (LLVM IR)**: the general-purpose bulk.
- **Link time (LTO/ThinLTO)**: cross-module inlining and devirtualization. **ThinLTO** is
  the scalable variant, using summaries rather than merging everything into one module.
- **Runtime (JIT)**: speculative optimization using real profile data (§9.3 → `language-runtimes-interpreters-and-jits`).
- **PGO/BOLT**: profile-guided layout, applied to already-linked binaries.

---

## §7. Code Generation and Backends

### 7.1 Choosing a backend

| Backend | Best for | Trade-offs |
|---|---|---|
| **LLVM** | Production compilers wanting best-in-class optimization and broad targets | **Excellent codegen; slow compilation; a very large C++ dependency; API churn across versions** |
| **Cranelift** | Fast compilation, JIT, WebAssembly, debug builds | Written in Rust; fast; **less optimization than LLVM**; used by Wasmtime and as rustc's alternative backend |
| **GCC (libgccjit / gccrs-style frontend)** | Targets LLVM doesn't support; GPL ecosystem | Fewer frontends use it; different integration model |
| **Custom** | Full control, no dependency, fast debug builds, unusual targets | You now own instruction selection, register allocation, and every target |
| **WebAssembly** | Portability, sandboxing, plugins | §7.5 |
| **Transpile to C** | Maximum portability, bootstrap | You inherit C's UB and lose debuggability |
| **Bytecode + interpreter** | Fastest path to a working language | Slow; see §9 → `language-runtimes-interpreters-and-jits` |

**[VERSIONED — a live and instructive case study.] The LLVM-dependency question is being
tested in public right now by two projects:**
- **Zig** is deliberately reducing its LLVM dependency. Its **self-hosted x86_64 backend
  became the default for Debug mode**, with dramatic reported compile-time wins (a hello
  world going from ~22.8 s to ~275 ms; the Zig compiler itself from ~75 s to ~20 s). By
  2026, Zig's own release notes state that **its x86 backend is more robust than its LLVM
  backend in terms of implementing the Zig language**, and a tracking issue exists to
  remove LLVM, LLD, and Clang libraries from the compiler entirely. The stated payoff:
  "all our bugs are belong to us," trivial bootstrapping, and in-place incremental binary
  patching. Zig 0.16 (April 2026) added architectures — Alpha, KVX, MicroBlaze, OpenRISC,
  PA-RISC, SuperH — while *removing* Solaris, AIX, and z/OS support.
- **rustc** keeps LLVM as the production backend but ships **Cranelift** as an alternative
  for debug builds. Measured on large real projects (Zed, Tauri, hickory-dns), it delivers
  roughly a **20% reduction in code generation time**, translating to about a **5% speedup
  in total clean-build time**. Note the ratio: **codegen is only ~25% of the wall clock**,
  which is the honest counterargument to "replace LLVM to get fast builds." rustc also
  maintains a GCC backend, and abstracts over all three via `rustc_codegen_ssa`.

**[DURABLE] The generalizable lesson: LLVM gives you world-class output slowly. If your
users' dominant pain is edit-compile-test latency rather than runtime performance, a
second, fast, dumb backend is a better investment than optimizing your LLVM usage** — and
architecting for *two* backends from the start (as rustc did with `rustc_codegen_ssa`) is
much cheaper than retrofitting.

### 7.2 Instruction selection

Map IR operations to target instructions. Approaches: **macro expansion** (one IR op → a
fixed instruction sequence; simple, poor code), **tree pattern matching with dynamic
programming** (Aho–Johnson / BURS / iburg; optimal per-tree), **DAG-based** (LLVM
SelectionDAG — handles shared subexpressions), and **GlobalISel** (LLVM's newer
IR-to-machine-IR framework, designed to be faster and more incremental than SelectionDAG).

### 7.3 Register allocation

**[DURABLE] Optimal register allocation is NP-complete** (it's graph colouring — Chaitin's
1981 reduction). The practical approaches:

| Algorithm | Notes |
|---|---|
| **Linear scan** | Fast, decent output. **The right choice for a JIT or a debug-build backend.** Poletto & Sarkar |
| **Graph colouring** (Chaitin–Briggs) | Better output, slower. Traditional AOT choice |
| **SSA-based** | Interference graphs of SSA programs are **chordal**, so colouring is polynomial. An elegant and increasingly common result worth knowing |
| **PBQP** | Partitioned boolean quadratic programming; handles irregular architectures |

The hard parts are always: **spilling** (choosing what to evict — usually by loop depth and
next-use distance), **coalescing** (removing redundant moves without making the graph
uncolourable), **live-range splitting**, and **calling-convention and register-class
constraints** (which are far more of the real work than the colouring algorithm).

### 7.4 The ABI

**[DURABLE] The ABI is the hardest under-appreciated part of a back end**, and getting it
wrong produces bugs that only appear when crossing a language boundary. You must specify:
calling convention (argument registers, stack layout, who cleans up), struct passing rules
(by value in registers? by hidden pointer? the System V x86-64 classification algorithm is
genuinely intricate), return values (including small aggregates), name mangling, stack
alignment (16 bytes on x86-64 SysV — violate it and SSE code faults), varargs, exception
unwinding tables, and TLS.

> **⚠️ GOTCHA — you cannot invent your own ABI and also interoperate.** If you want C FFI
> (you do — §8.5 → `language-runtimes-interpreters-and-jits`), you must implement the platform ABI exactly, including its ugly corners.
> Most new languages have at least one embarrassing "we passed a small struct wrong on
> Windows ARM64" bug.

### 7.5 WebAssembly as a target

**[VERSIONED — this changed materially in 2026.]** Wasm is a genuinely good compilation
target: a stack machine with structured control flow, a linear memory, and strong
sandboxing guarantees.

**WASI 0.3.0 was released on 11 June 2026**, and the change is architectural rather than
incremental: **native async is moved down into the Component Model's canonical ABI**, with
`async func`, `stream<T>`, and `future<T>` as primitives. The `wasi:io` package —
pollables, input-streams, output-streams — **is removed entirely**, absorbed into the
canonical ABI. The motivating problem is worth understanding because it's a general
lesson in interface design: under WASI 0.2, a `pollable` was a resource scoped to a single
component instance, so in a chain A→B→host, **component B could not forward the host's
wake-ups to A** and had to actively poll just to relay readiness. In 0.2 every component
needed its own event loop with no way to coordinate. Most 0.2→0.3 signature changes are
described as mechanical.

**What this means for a language implementer**: the **Component Model** plus **WIT**
(the interface definition language) plus the canonical ABI turns Wasm from "a module with
ad-hoc host glue" into a **typed, language-agnostic service boundary** — a component
declares what it needs and provides, and the host or linker wires the edges. Bindings
generators can now emit *idiomatic async* bindings per language. Wasmtime 45 ran the RC;
Wasmtime 46 ships 0.3.0. **A formally specified Component Model 1.0 is the next milestone**,
previewed at the Bytecode Alliance Plumbers Summit and Wasm I/O 2026.

**The honest caveats**, which the ecosystem states openly: **WASI still has no native
multi-threading**, which quietly rules out whole categories of compute-heavy server
workloads; **WASI 1.0 is planned but not shipped**; and adoption remains concentrated in
specific niches (edge functions, plugin systems) rather than general server compute —
Fermyon's edge platform and wasmCloud deployments are real, but they are chosen niches.
Note also that reporting on WASI versions is unusually inconsistent — you will find
sources in 2026 simultaneously describing 0.3 as "released," "in preview," and "the next
milestone." Check `wasi.dev` directly.
