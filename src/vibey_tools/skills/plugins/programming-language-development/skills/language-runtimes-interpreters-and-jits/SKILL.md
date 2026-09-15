---
name: language-runtimes-interpreters-and-jits
description: "Use when building a language runtime or execution engine. Covers memory management and garbage collection (tracing, generational, reference counting, ownership), the object model, concurrency models (threads, async/await, green threads, actors), errors and unwinding, FFI, the interpreter performance ladder, interpreter techniques worth knowing (bytecode design, dispatch, inline caching), JIT compilation (baseline and optimizing tiers, tracing, deoptimization), and the bootstrapping and trust problem."
---

# Programming Language Development: Runtime Systems, Interpreters, and JITs

> **Part 3 of 5** of the *Programming Language Development* reference (plugin `programming-language-development`), covering §8–§9. Sibling skills: `language-design-parsing-and-types` (§0–§4), `language-irs-optimization-and-backends` (§5–§7), `language-diagnostics-tooling-and-evolution` (§10–§14), `language-development-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §8. Runtime Systems

### 8.1 Memory management

| Strategy | Cost | Used by |
|---|---|---|
| **Manual** | Zero runtime cost; UAF, leaks, double-free | C |
| **RAII + ownership** | Zero runtime cost; compile-time complexity | C++, Rust |
| **Reference counting** | Cheap latency, no pauses; **cycles leak**; refcount traffic is real, and atomic refcounts are expensive | Swift (ARC), CPython, Objective-C |
| **Tracing GC** | Handles cycles; throughput good; **pauses**; needs precise root/pointer identification | Java, Go, C#, JS, Haskell |
| **Arena/region** | Very fast alloc, bulk free; needs a lifetime discipline | Zig allocators, compilers themselves, request-scoped servers |

**Tracing GC design axes** [DURABLE]: **generational** (most objects die young — the
single most valuable GC insight ever), **moving vs. non-moving** (moving enables bump
allocation and compaction but requires precise pointer maps and read/write barriers),
**concurrent/incremental** (Go's low-latency collector; ZGC and Shenandoah's sub-millisecond
pauses), and **conservative vs. precise** (Boehm scans the stack conservatively — easy to
retrofit onto C, but can retain garbage and cannot move objects).

**[DURABLE] Your GC choice constrains your language design, not just your runtime.**
Precise GC requires the compiler to emit **stack maps** at every safepoint, which
constrains your calling convention, your optimizer (it must maintain the maps across
transformations), and your FFI (native code doesn't have maps — hence handles/pinning).
Deciding on GC late is not really possible.

### 8.2 The object model

Decisions here propagate everywhere: boxed vs. unboxed values (and whether small integers
are tagged — **NaN-boxing** is the standard trick in dynamic-language VMs, packing pointers
and integers into the unused bit patterns of IEEE-754 doubles), object headers (type,
GC mark bits, hash, lock word — every byte is multiplied by every object), field layout
(declared order or optimized packing; Rust reorders by default, C does not), method
dispatch (vtable, inline cache, hash lookup), and **hidden classes / shape trees**
(V8's mechanism for making dynamically-typed property access fast — arguably the single
biggest idea in modern dynamic-language performance).

### 8.3 Concurrency

| Model | Notes |
|---|---|
| OS threads + locks | Simple mapping; expensive; data races |
| **Green threads / goroutines** | M:N scheduling; **requires runtime support and growable stacks**; Go's segmented→copying stack evolution is instructive |
| **async/await** | No runtime threads needed; **function colouring** |
| Actors | Isolation by construction (Erlang, Akka) |
| CSP / channels | Go, Occam |
| Structured concurrency | Lifetimes of tasks bounded by scope. **The clear modern direction** — Kotlin, Swift, Java's virtual threads, Trio |
| Algebraic effects | OCaml 5 — concurrency without colouring (§4.9 → `language-design-parsing-and-types`) |

**[CONTESTED] Function colouring.** async/await splits your function universe in two:
async functions can only be awaited by async functions, so any library that becomes async
forces its callers to. *Against*: it fragments ecosystems (Python and Rust both have
visible sync/async library splits), and it's an ad-hoc effect system with none of the
polymorphism. *For*: it's explicit about where suspension happens, needs no runtime, works
in `no_std` and embedded contexts, and makes cost visible. Green threads/virtual threads
avoid colouring at the cost of requiring runtime support — which is precisely why Rust
removed green threads before 1.0 and Java added them in 2023.

### 8.4 Errors and unwinding

**Exceptions**: zero-cost when not thrown (table-driven unwinding; the tables live in
`.eh_frame`/`.gcc_except_table`), expensive when thrown. Requires unwinding-table
generation in the back end and destructor/cleanup landing pads — this is a *significant*
back-end feature, not a library concern.

**Result/Option types**: explicit, composable, no unwinder needed, but verbose without
sugar (`?` in Rust, `try` in Swift/Zig). **[DURABLE] The ergonomics live or die on the
propagation operator** — Go's pre-1.13 `if err != nil` verbosity is the standard cautionary
example.

**Panics/aborts** for unrecoverable errors. Decide early whether panics unwind or abort;
it affects the ABI, FFI safety (**unwinding across an FFI boundary into C is UB unless
both sides agreed**), and whether destructors run.

### 8.5 FFI

**[DURABLE] Your C FFI is the interface to forty years of existing software, and it will
be used more than you expect.** The hard parts: type mapping (especially strings — length
vs. NUL-terminated, and encoding), ownership across the boundary (who frees?), callbacks
into managed code (GC roots! stack maps!), thread attachment, error propagation, and
**never letting an exception or panic escape into C**.

Design decisions worth copying: Rust's `extern "C"` + `#[repr(C)]` (explicit ABI opt-in
per type and function), Zig's ability to `@cImport` C headers directly, and Swift's
generated header approach. **The single best decision is making the unsafe boundary
syntactically visible** so it's greppable and reviewable.

---

## §9. Interpreters and JITs

### 9.1 The performance ladder

```
AST tree-walking       1×      Easiest to write. Correct. Slow. Start here.
Bytecode + switch      3–10×   The standard baseline.
Computed goto/threaded 1.5–2×  over switch. Better branch prediction. GCC/Clang extension.
Register bytecode      1.2–1.5× over stack bytecode. Fewer dispatches.
Inline caching         2–10×   on dynamic dispatch. The big win for dynamic languages.
Template/baseline JIT  2–5×    over interpreter. Fast to compile, no optimization.
Optimizing JIT         10–100× With type feedback + speculation + deopt.
AOT + PGO              comparable to JIT for static languages, no warmup
```

### 9.2 Interpreter techniques worth knowing

- **Direct threading / computed goto** — replace the dispatch `switch` with a jump table
  and a `goto *ip` at the end of each handler, giving the branch predictor one indirect
  branch per opcode instead of one shared branch. Typically 20–50%.
- **Superinstructions** — fuse common opcode pairs into one, cutting dispatch count.
- **Inline caching** — cache the result of a dynamic lookup at the call site.
  Monomorphic → polymorphic → megamorphic. **This plus hidden classes (§8.2) is why
  JavaScript is fast.**
- **NaN-boxing / pointer tagging** — avoid allocating for small values.
- **Register-based bytecode** — Lua's design; fewer instructions than a stack machine.

### 9.3 JIT

**Tiered execution** is the standard architecture: interpret first (fast start, gather
profile), then a baseline JIT for warm code, then an optimizing JIT for hot code, using
the profile to **speculate** — assume this call site is monomorphic, assume this integer
doesn't overflow, assume this type is stable — and **guard** each assumption, with
**deoptimization** back to the interpreter when a guard fails.

**[DURABLE] Deoptimization is the hardest part of a JIT.** You must be able to reconstruct
the exact interpreter state (locals, stack, PC) at any guard from optimized machine-code
state — which means every optimization must maintain that mapping. Get it wrong and you
get silent wrong answers, the worst possible failure mode.

**JIT-specific concerns**: W^X (memory must never be simultaneously writable and
executable), icache invalidation on ARM, on-stack replacement (OSR) for long-running loops,
code cache management, and the fact that a JIT is a **JIT-spraying attack surface**.

### 9.4 The bootstrapping and trust problem

If you write your compiler in your own language, you need an existing binary to build it —
and **Ken Thompson's "Reflections on Trusting Trust" (1984)** shows a compiler can be
backdoored such that the backdoor survives recompilation from clean source and is invisible
in the source. The practical answers: keep a documented bootstrap chain from a
minimal seed (Zig cites trivial bootstrapping as a *benefit* of dropping LLVM),
**reproducible builds**, and **diverse double-compiling** (David A. Wheeler's technique —
compile with two independent compilers and compare the outputs).
