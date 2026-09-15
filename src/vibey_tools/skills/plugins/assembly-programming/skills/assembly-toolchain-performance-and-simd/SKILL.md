---
name: assembly-toolchain-performance-and-simd
description: "Use when wiring assembly to C (calling conventions and ABIs: System V, Windows x64, AAPCS64, RISC-V), choosing or fighting an assembler (GAS vs NASM, AT&T vs Intel syntax, linkers, objdump), reading disassembly and recognizing compiler patterns, or optimizing at the instruction level. Covers the out-of-order/superscalar mental model, latency vs throughput, caches and memory, branch prediction, alignment, and SIMD/vector programming — SSE/AVX/AVX-512/AVX10, NEON/SVE2/SME, RISC-V RVV — and how to write SIMD well."
---

# Assembly Programming: ABIs, Toolchain, Disassembly, Performance, and SIMD

> **Part 2 of 4** of the *Assembly Programming* reference (plugin `assembly-programming`), covering §6–§10. Sibling skills: `assembly-fundamentals-and-isas` (§0–§5), `assembly-systems-crypto-and-inline` (§11–§14), `assembly-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §17 → `assembly-reference` for the currency snapshot and what goes stale first.

> **How to read this.** Reference, not tutorial. Sections are independent. Three markers:
> - **[DURABLE]** — machine organization, algorithms, or a lesson that has held since the
>   1970s. Does not expire.
> - **[ISA]** — specific to x86-64, AArch64, RISC-V, or a particular microarchitecture.
>   Verify against the vendor's current manual.
> - **[CONTESTED]** — practitioners genuinely disagree, usually about how much hand-written
>   assembly is justified.
>
> **⚠️ GOTCHA** boxes mark the mistakes that produce silent corruption, ABI violations,
> or code that is slower than the C you replaced.
>
> **The three framings that organize everything below:**
> 1. **The instruction set is an interface, not the machine.** The CPU you're actually
>    programming is out-of-order, superscalar, speculative, and cached. Your instructions
>    are decoded into µops, reordered, and executed in parallel. Reasoning about assembly
>    as "the CPU does this, then this" is wrong in ways that make your optimizations wrong.
> 2. **Reading assembly is a hundred times more common than writing it, and more
>    valuable.** Most of the return here comes from understanding compiler output,
>    debugging an optimized crash, or reverse-engineering a binary.
> 3. **When you write assembly, you are taking on the compiler's job permanently.** No
>    retargeting, no auto-vectorization, no new-CPU tuning, and no help from the next
>    twenty years of compiler improvements. That's the real cost, and it's paid in
>    maintenance rather than in the initial write.

---

## §6. Calling Conventions and ABIs

**[DURABLE] The ABI is the contract, and violating it produces bugs that appear far from
the cause.** You must know: which registers pass arguments, which are caller- vs.
callee-saved, where the return value goes, stack alignment, how structs are passed, and
how varargs work.

| | **System V AMD64** (Linux/macOS/BSD) | **Windows x64** | **AAPCS64** (ARM64) | **RISC-V** |
|---|---|---|---|---|
| Int args | rdi, rsi, rdx, rcx, r8, r9 | **rcx, rdx, r8, r9** only | x0–x7 | a0–a7 |
| FP args | xmm0–7 | xmm0–3 | v0–v7 | fa0–fa7 |
| Return | rax (rdx:rax for 128) | rax | x0 (x0,x1) | a0 (a0,a1) |
| Callee-saved | rbx, rbp, r12–r15 | rbx, rbp, rdi, rsi, r12–r15, **xmm6–15** | x19–x28, v8–v15 (**low 64 bits only**) | s0–s11, fs0–fs11 |
| Stack align at call | **16 bytes** | 16 bytes | **16 bytes** | 16 bytes |
| Special | **red zone: 128 bytes below rsp** usable without adjusting | **32-byte shadow space** the caller must allocate | x18 platform-reserved on some OSes | — |

> **⚠️ GOTCHA — the four ABI mistakes that account for most hand-written-assembly bugs:**
> 1. **Clobbering a callee-saved register** without saving it. The corruption surfaces in
>    the *caller*, arbitrarily later.
> 2. **Misaligning the stack.** SSE/NEON instructions fault or silently slow down, and
>    the failure appears inside an unrelated library function.
> 3. **Assuming System V on Windows** (or vice versa). Completely different argument
>    registers, plus Windows' shadow space and xmm6–15 preservation.
> 4. **AArch64 `v8–v15`: only the low 64 bits are callee-saved.** The upper halves are
>    caller-saved. This one bites SIMD code specifically.
>
> Also: the **red zone does not exist in kernel or interrupt context** (Linux compiles the
> kernel with `-mno-red-zone` for exactly this reason), and varargs on System V requires
> `al` to hold the number of vector registers used.

**Name mangling and symbol visibility**: C symbols may get a leading underscore (Darwin,
older platforms) and C++ names are mangled — use `extern "C"` and check with `nm`.

---

## §7. Assemblers and Toolchain

### 7.1 The syntax split

**[DURABLE] Two syntaxes for x86, and the operand order is reversed.** This causes more
confusion than any other single thing in x86 assembly.

```asm
; Intel syntax (NASM, MASM, and `objdump -M intel`)     DEST, SRC
mov  rax, rbx
mov  rax, [rbx + rcx*8 + 16]
add  rax, 1

# AT&T / GAS syntax (default GNU)                        SRC, DEST
movq %rbx, %rax
movq 16(%rbx,%rcx,8), %rax
addq $1, %rax          # % on registers, $ on immediates, suffix for size
```
AArch64 and RISC-V have only one syntax each, which is one of several reasons they're
pleasanter to learn.

### 7.2 The tools

| Tool | Use |
|---|---|
| **GAS** (`as`, via `gcc`/`clang`) | The default on Unix. AT&T by default; `.intel_syntax noprefix` available |
| **NASM** / **YASM** | Intel syntax, standalone, excellent macro system. The x86 favourite |
| **Clang's integrated assembler** | Now the default in the LLVM toolchain; handles both syntaxes |
| **MASM** (`ml64`) | Windows/MSVC |
| **`objdump -d`**, **`llvm-objdump`** | Disassembly |
| **Ghidra**, **IDA Pro**, **Binary Ninja**, **radare2/rizin** | Reverse engineering with decompilation |
| **Compiler Explorer (godbolt.org)** | **The single most valuable tool in this whole document.** See §8 |
| **`perf`**, **VTune**, **uProf**, **Instruments** | Profiling with hardware counters |
| **LLVM-MCA**, **uiCA**, **OSACA** | Static throughput/latency analysis of a loop |
| **`gdb`/`lldb`** | `layout asm`, `si`, `info registers`, `x/i $pc` |

**Directives you need**: `.text`/`.data`/`.bss`/`.rodata`, `.global`, `.align`/`.p2align`,
`.byte`/`.word`/`.quad`, `.asciz`, `.type`/`.size` (**required for correct ELF symbols and
for the profiler to attribute samples**), and **CFI directives** (`.cfi_startproc`,
`.cfi_def_cfa_offset`, `.cfi_offset`, `.cfi_endproc`).

> **⚠️ GOTCHA — omit CFI and your function becomes invisible to unwinding.** Backtraces
> stop at your function, C++ exceptions cannot propagate through it, and profilers
> mis-attribute its samples. Hand-written assembly without CFI is a debugging black hole,
> and it's the most commonly skipped step.
CHUNKEOF
echo ok; wc -l /home/claude/assembly-programming.md 2>/dev/null || true

---

## §8. Reading Disassembly

**[DURABLE] This is the highest-value assembly skill, and most people who "know assembly"
mean this.**

### 8.1 The workflow

1. **Compiler Explorer (godbolt.org)** — paste source, pick a compiler and flags, watch the
   assembly change. Colour-coded source↔asm mapping. **If you want to learn assembly in
   2026, this is where you do it.**
2. `gcc -S -O2 -masm=intel -fverbose-asm` for local work.
3. `objdump -d --no-show-raw-insn -M intel binary` for shipped binaries.
4. `perf annotate` to see assembly with sample counts attached — *this* is how you find the
   hot instruction.

### 8.2 Recognizing patterns

```asm
; array indexing: a[i] where a is int32*
mov  eax, [rdi + rsi*4]

; a loop the compiler unrolled and vectorized (the give-away is the wide moves)
.L4:
  movdqu xmm0, [rdi + rax]
  paddd  xmm0, xmm1
  movdqu [rdi + rax], xmm0
  add    rax, 16
  cmp    rax, rdx
  jne    .L4

; a switch compiled to a jump table
  cmp   edi, 5
  ja    .Ldefault
  jmp   [.Ltable + rdi*8]

; a division by a constant, strength-reduced to multiply-and-shift
  mov   rax, 0x5555555555555556   ; magic number for /3
  imul  rdx
  ...

; a tail call (jmp, not call — no new stack frame)
  jmp   other_function
```

**[DURABLE] What surprises people reading `-O2` output for the first time:** variables
don't exist (they're in registers, or gone), the source line order is scrambled, functions
have been inlined away, loops are unrolled and vectorized, dead code is deleted entirely,
and **the debugger's line numbers are approximate at best**. This is normal and correct —
it is also why "it works in debug, fails in release" is usually a latent bug (UB) rather
than a compiler bug.

---

## §9. Performance

### 9.1 The mental model that's actually right

**[DURABLE] A modern core is a dataflow machine wearing a sequential ISA.** It fetches
many instructions ahead, renames away false dependencies, and executes whatever is ready.
So:

**What costs you, in descending order:**
1. **Cache misses.** ~4 cycles L1, ~12 L2, ~40 L3, **~200–300+ cycles DRAM.** A single
   main-memory miss costs more than a hundred arithmetic instructions. **Memory layout is
   the optimization.**
2. **Branch mispredictions.** ~15–20 cycles of wasted work. Predictable branches are nearly
   free; unpredictable ones are catastrophic — which is why `cmov`/`csel` exists.
3. **The critical dependency chain.** If each iteration depends on the last, you get
   latency, not throughput. **Break the chain with multiple accumulators.**
4. **Long-latency instructions**: division (20–100 cycles), some transcendentals, `pdep`
   on the wrong microarchitecture.
5. **Port contention / execution-unit throughput.**
6. Instruction count. Last.

### 9.2 Latency vs. throughput — the distinction beginners miss

**Latency** = cycles until the result is available to a dependent instruction.
**Throughput** (reciprocal throughput) = cycles between issuing independent instances.

A multiply might be **latency 4, throughput 0.5** — four cycles to get an answer, but you
can start two per cycle. So:
```asm
; SLOW: one accumulator, serialized on the add's latency
.loop:  add rax, [rsi + rcx*8]
        inc rcx
        jne .loop

; FAST: four accumulators, four independent chains, saturates the ports
.loop:  add rax, [rsi + rcx*8]
        add rbx, [rsi + rcx*8 + 8]
        add r8,  [rsi + rcx*8 + 16]
        add r9,  [rsi + rcx*8 + 24]
        add rcx, 4
        jne .loop
        ; then combine rax+rbx+r8+r9
```
**[DURABLE] This "multiple accumulators to break the dependency chain" pattern is the
single most reusable optimization in hand-written assembly**, and it applies identically to
scalar and SIMD code.

**Get the numbers from**: **Agner Fog's instruction tables** (the canonical reference for
x86 latency/throughput/ports across every microarchitecture), **uops.info** (automated and
exhaustive), Intel's and AMD's optimization manuals, and Arm's Software Optimization Guides
per core.

### 9.3 Memory

- **Cache line = 64 bytes** on essentially everything current. This is the fundamental
  unit; internalize it.
- **Sequential access is prefetched automatically; random access is not.** A linked list
  and an array with the same asymptotics differ by 10× in practice.
- **False sharing**: two threads writing different variables *in the same cache line*
  ping-pong the line between cores and destroy scaling. Pad to 64 (or 128 — some
  prefetchers work in pairs) bytes.
- **Structure of Arrays beats Array of Structures** for SIMD, almost always.
- **Non-temporal stores** (`movntdq`, `stnp`) bypass the cache for streaming writes you
  won't re-read. Powerful and easy to misuse.
- **Software prefetch** (`prefetcht0`, `prfm`) helps only when the hardware prefetcher
  can't see the pattern and you can issue it far enough ahead. **Usually it does nothing
  or hurts; measure.**

### 9.4 Branches

- Predictable branches ≈ free. Unpredictable ≈ 15–20 cycles.
- **Branchless with `cmov`/`csel`** trades a mispredict for a data dependency — a win when
  unpredictable, a loss when predictable (because it serializes what the predictor would
  have run ahead of).
- Loop alignment and target alignment sometimes matter; measure rather than cargo-cult.
- **⚠️ Do not use x86 branch-hint prefixes.** They've been ignored for two decades.

### 9.5 The rule

**[DURABLE] Measure, change one thing, measure again — on the actual target hardware.**
Assembly optimization without measurement is superstition, and the literature is full of
tricks that were true on a Pentium 4 and have been wrong ever since. Benchmark with real
data distributions, beware of the microbenchmark that keeps everything in L1, and be
suspicious of any speedup you can't explain mechanically.

---

## §10. SIMD and Vector

### 10.1 The two models

**[DURABLE] There are now two fundamentally different vector programming models, and this
is the biggest conceptual split in modern assembly.**

**Fixed-width SIMD** — the register is a known size at compile time. SSE (128), AVX (256),
AVX-512 (512), NEON (128). You write a main loop plus a **scalar epilogue** for the
remainder, and you recompile (or runtime-dispatch) for each width.

**Scalable/vector-length-agnostic (VLA)** — the register size is unknown at compile time
and discovered at runtime. **ARM SVE/SVE2** and **RISC-V RVV** both work this way, deriving
from the Cray vector tradition rather than from packed SIMD. The same binary runs on
hardware with different vector lengths without recompiling.

```asm
; RISC-V RVV: the canonical strip-mined loop — no epilogue needed
loop:
    vsetvli t0, a0, e32, m8      ; "give me up to a0 elements of 32-bit, LMUL=8"
                                 ; t0 = how many you actually got
    vle32.v v0, (a1)             ; load t0 elements
    vadd.vi v0, v0, 1
    vse32.v v0, (a2)
    sub  a0, a0, t0              ; decrement remaining
    slli t1, t0, 2
    add  a1, a1, t1
    add  a2, a2, t1
    bnez a0, loop
```
**[DURABLE] `vsetvli` returning the granted length is the whole idea**: the hardware tells
you how much it can do, the loop handles any remainder naturally, and **the tail-handling
code that dominates fixed-width SIMD simply disappears.** SVE achieves the same with
predication and `whilelt`.

RVV specifics worth knowing: **32 vector registers**; **VLEN** (implementation vector
length) ranges from 128 to 16384 bits in shipping implementations; **SEW** (element width)
and **LMUL** (register grouping: 1/8 … 8) are set dynamically by `vsetvli`, so the *same*
instruction encoding works across element types and widths.

### 10.2 The x86 SIMD landscape

```
MMX(dead) → SSE→SSE4.2 (128-bit, xmm) → AVX/AVX2 (256-bit, ymm, 3-operand VEX)
  → AVX-512 (512-bit, zmm0–31, 8 mask registers k0–k7, EVEX encoding)
    → AVX10 (the convergence effort, §17)
```
**Mask registers (k0–k7) are AVX-512's best feature** and are underappreciated: per-lane
predication with zeroing or merging, which makes tail handling and conditional lanes far
cleaner than the blend-based tricks required in AVX2.

> **⚠️ GOTCHA — AVX-512 fragmentation is the reason AVX10 exists.** Intel shipped AVX-512
> on some server parts, then **disabled it on hybrid consumer parts** because the E-cores
> didn't have it. AMD implemented it (double-pumped on Zen 4, full-width on Zen 5). Result:
> a decade where you couldn't assume 512-bit vectors on a desktop x86 CPU. §17 → `assembly-reference` has the
> 2026 state.

> **⚠️ GOTCHA — downclocking.** Heavy 512-bit AVX-512 use historically dropped clock
> frequency on Intel server parts, so a vectorized loop could slow the *rest* of the
> program down. Much improved on recent silicon, but **always measure whole-application
> throughput, not just the kernel.**

> **⚠️ GOTCHA — AVX/SSE transition penalties.** Mixing legacy SSE and VEX-encoded AVX
> without `vzeroupper` causes expensive state-transition stalls. **Emit `vzeroupper` before
> returning from AVX code to a caller that might use SSE.**

### 10.3 ARM SIMD

**NEON** (128-bit, v0–v31) is the universal baseline on AArch64 — always present, no
runtime check needed.

**SVE/SVE2** is scalable and predicated. **SME/SME2 (Scalable Matrix Extension)** adds
**ZA storage** and outer-product operations for matrix work, with `SMSTART`/`SMSTOP` to
enter and leave streaming mode.

**[VERSIONED]** Deployment as of 2026 is uneven and worth knowing precisely: **the Apple
M4 family was the first consumer-grade silicon to support both SVE2 and SME** (Apple's own
LLVM contribution specifies **Armv9.2-A** for M4 and confirms SME and SME2). Arm's
**Lumex** cores bring SME2 to Android; some competing custom cores shipped SME1 + SVE2
first. **Do not assume SVE2 or SME are present** — check `HWCAP`/`ID_AA64*` at runtime and
keep a NEON path.

### 10.4 Writing SIMD well

**[DURABLE, and this is the most important advice in the section] Use intrinsics, not
assembly, for SIMD.** You get the exact instructions you want *plus* register allocation,
scheduling, inlining, and constant folding for free. Hand-written SIMD assembly is
justified when you're fighting the register allocator on a large kernel, and rarely
otherwise.

The techniques: **Structure-of-Arrays** layout, alignment where it matters, handling the
tail (or using a VLA ISA and not needing to), **shuffles/permutes** as the hard part,
horizontal reductions (expensive — keep them out of the loop), and **runtime dispatch**
(check CPUID/HWCAP once, select a function pointer, and note that indirect call overhead
means you dispatch per *buffer*, not per element).
