---
name: assembly-systems-crypto-and-inline
description: "Use when writing systems-level assembly (interrupt handlers, context switches, syscall stubs, boot code, privileged instructions), cryptographic or constant-time assembly (the three rules, the hardware contract and why it changed, going beyond hand-writing), inline assembly and compiler intrinsics (GCC/Clang extended asm constraints and clobbers, when to prefer intrinsics), or debugging, testing, and verifying hand-written assembly with GDB, sanitizers, and differential testing."
---

# Assembly Programming: Systems, Constant-Time, Inline Assembly, and Debugging

> **Part 3 of 4** of the *Assembly Programming* reference (plugin `assembly-programming`), covering §11–§14. Sibling skills: `assembly-fundamentals-and-isas` (§0–§5), `assembly-toolchain-performance-and-simd` (§6–§10), `assembly-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §11. Systems Assembly

**[DURABLE] Some things simply cannot be written in a high-level language**, and this is
where assembly is unavoidable rather than merely faster:

- **Reset/boot code** — before the stack, the data section, or any C runtime exists.
- **Interrupt and exception vectors** — save volatile state, switch stacks, call the
  handler, restore precisely, return with the special instruction (`iret`, `eret`, `mret`).
- **Context switching** — save one thread's callee-saved registers and stack pointer,
  load another's. Fundamentally unexpressible in C.
- **Syscall entry/exit stubs**.
- **`setjmp`/`longjmp`, coroutines, stack switching, unwinding**.
- **Atomics and lock primitives** where you need exact instruction selection.
- **Self-modifying code, JIT emission, trampolines, PLT stubs**.
- **Cache and TLB maintenance** (`clflush`, `wbinvd`, `dc civac`, `tlbi`, `sfence.vma`) and
  memory barriers.

```asm
; Linux x86-64 syscall  (write(1, msg, len))
mov rax, 1          ; syscall number
mov rdi, 1          ; fd
mov rsi, msg
mov rdx, len
syscall             ; ⚠️ CLOBBERS rcx and r11 — the ABI differs from a function call
```
> **⚠️ GOTCHA — the syscall ABI is not the function-call ABI.** On x86-64 Linux, the
> **4th argument is `r10`, not `rcx`** (because `syscall` destroys `rcx`), and `rcx` and
> `r11` are clobbered. On AArch64 the number goes in `x8` and the instruction is `svc #0`.
> Getting this wrong produces bafflingly wrong syscall behaviour.

**JIT-specific concerns**: **W^X** (never map memory writable and executable
simultaneously — use dual mapping or `mprotect` transitions; **macOS on Apple Silicon
requires `pthread_jit_write_protect_np`**), and **instruction-cache invalidation** — on
ARM and RISC-V, writing bytes is not enough; you must flush D-cache to the point of unity
and invalidate I-cache (`dc cvau` / `ic ivau` / `isb`, or `fence.i`). **x86 has coherent
I-cache and doesn't need this**, which is exactly why JIT code that works on x86 breaks
mysteriously when ported.

---

## §12. Cryptographic and Constant-Time Assembly

**[DURABLE] This is the strongest remaining justification for hand-written assembly, and
the reason is that the compiler is actively working against you.** An optimizing compiler
is free to turn your carefully branchless code back into a branch, and there is no
standard way in C to say "don't."

### 12.1 The three rules

1. **Never branch on secret data.**
2. **Never index memory at a secret-dependent address** (cache-timing attacks — Bernstein's
   AES cache-timing work is the canonical demonstration).
3. **Never use variable-latency instructions on secret data** — historically division, and
   on some hardware multiplication.

Tools: `cmov`/`csel` (§2.3 → `assembly-fundamentals-and-isas`, §3.2 → `assembly-fundamentals-and-isas`), masking (`mask = -(cond & 1)` then
`r = (a & mask) | (b & ~mask)`), and constant-time comparison that accumulates differences
with OR rather than returning early.

### 12.2 The hardware contract — and why it changed

**[VERSIONED, and this is genuinely important and under-known.]** For decades rule 3 rested
on documentation and microbenchmarks with **no guarantee for future microarchitectures**.
That changed with explicit vendor contracts:

- **Arm DIT** (`PSTATE.DIT`, since Armv8.4) — when set, the architecture requires that the
  timing of instructions in the DIT subset is insensitive to the *data values* in their
  registers, and that load/store timing is insensitive to the data being loaded or stored.
- **Intel DOIT** (`IA32_UARCH_MISC_CTL` bit 0, "data operand independent timing") — the
  same idea for a documented instruction subset. **Intel explicitly does not recommend
  enabling it globally** because of the performance cost; it's meant to be enabled only for
  code already written to be constant-time.
- **RISC-V has this in the ISA itself**: **`Zkt`** (scalar) and **`Zvkt`** (vector) attest
  that their instruction subsets have data-independent execution latency — and **Zvkt is
  mandatory in RVA23**.

**The part that catches people out:** on **Intel, the guarantees held by default only for
microarchitectures earlier than Ice Lake (Core) and Gracemont (Atom)**. On Ice Lake,
Gracemont, and later, they are **not provided by default** and must be explicitly enabled
via DOIT. Meanwhile the DOIT bit is an **MSR — kernel-only**, whereas Arm's DIT is a cheap
*unprivileged* `msr` a user-space program can set itself. Linux enabled DIT for arm64 in
**v6.2 but only in the kernel**, leaving user space to opt in.

> **⚠️ GOTCHA — read Arm's DIT guarantee precisely.** It requires timing to be independent
> of *the registers the instruction explicitly uses*. Researchers have pointed out it does
> **not** obviously cover values in registers the instruction doesn't reference, and it
> makes no statement about **data memory-dependent prefetchers (DMPs)** — the mechanism
> behind attacks like GoFetch. **Intel's DOIT, by contrast, explicitly does cover
> data-dependent prefetchers.** These are not equivalent guarantees, and the difference
> matters for real attacks.

### 12.3 Beyond hand-writing

The state of the art is moving toward **verified** rather than merely careful:
**Jasmin** (a language and verification framework for high-assurance crypto, extended to
prove that only DOIT-subset instructions touch secret data — *including under speculative
execution*), **Serberus**, **Vale**, and formally-verified libraries like
**HACL\*** and **fiat-crypto**. **[VERSIONED]** LLVM is also gaining **constant-time
intrinsics** (lowering to `CSEL` on AArch64, masked arithmetic where no constant-time
instruction exists), which maintainers of Rust Crypto, BearSSL, and PuTTY have expressed
interest in adopting **to replace their current inline-assembly workarounds** — which, if
it lands broadly, removes one of assembly's last unavoidable use cases.

**Also use the hardware crypto instructions**: AES-NI, ARMv8 Crypto Extensions, RISC-V
Zvk*. They are faster *and* constant-time by construction, which is the rare case where
the fast path and the safe path coincide.

---

## §13. Inline Assembly and Intrinsics

### 13.1 Prefer intrinsics

**[DURABLE]** Intrinsics give you the specific instruction while keeping register
allocation, scheduling, inlining, and constant propagation. Inline assembly gives up all
of that and requires you to describe your effects to the compiler correctly — which is
where the bugs are.

### 13.2 GCC/Clang extended asm, and how to get it right

```c
__asm__ volatile (
    "addq %[b], %[a]"          // template
    : [a] "+r" (x)             // outputs:  "+" = read-write
    : [b] "r"  (y)             // inputs
    : "cc", "memory"           // CLOBBERS — the part people get wrong
);
```
**The constraint letters that matter**: `r` (any GPR), `m` (memory), `i` (immediate),
`=` (write-only output), `+` (read-write), `&` (**early-clobber** — written before all
inputs are consumed).

> **⚠️ GOTCHA — the four inline-asm failure modes, in order of how much time they waste:**
> 1. **Missing `"memory"` clobber** when the asm reads or writes memory the compiler
>    thinks it knows about → the compiler caches a stale value in a register, and the bug
>    appears only at `-O2`.
> 2. **Missing `"cc"` clobber** when you modify flags → the compiler reuses flags it
>    thought were still valid.
> 3. **Missing `&` early-clobber** → the compiler assigns an output and an input to the
>    same register, and your asm overwrites the input before reading it.
> 4. **Missing `volatile`** on asm with side effects but no used output → the compiler
>    deletes it, or hoists it out of a loop.
>
> All four produce code that works at `-O0` and fails at `-O2`, which is the worst
> possible debugging experience.

**MSVC has no inline assembly for x64** — you use intrinsics or a separate `.asm` file
assembled by MASM. This is a real portability constraint on cross-platform projects.

**Naked functions / separate `.s` files** are cleaner than large inline blocks: you get
full control, real assembler syntax, proper CFI, and the code is testable and profilable.

---

## §14. Debugging, Testing, and Verification

**Debugging**: `gdb`/`lldb` with `layout asm` / `si` / `info registers` / `x/i $pc`;
`disassemble /s` to interleave source; hardware watchpoints; `rr` for reverse debugging
(x86 Linux — transformative for "how did this register get that value"); Intel PT / Arm
CoreSight for execution traces; and single-stepping is the ultimate ground truth.

**Testing hand-written assembly**:
- **Differential testing** against a simple, obviously-correct C reference over random
  inputs. **This is the single most valuable practice** and catches the overwhelming
  majority of real bugs.
- **Exhaustive testing on small input spaces** where feasible.
- **Edge cases**: zero length, one element, unaligned, maximum values, sign boundaries,
  overlapping buffers, and the tail-handling path (which is where SIMD bugs concentrate).
- **Sanitizers won't help you.** ASan and MSan don't instrument your assembly; you're
  outside their model.
- **Valgrind can still catch** bad memory access and uninitialized-value use in some cases.
- **Verify ABI compliance mechanically**: a wrapper that fills every callee-saved register
  with a poison value, calls your routine, and checks them afterwards will catch clobbering
  bugs that otherwise surface as corruption three functions away.
- **Test on multiple microarchitectures.** Something that's a win on one core is a loss on
  another, and something that's *correct* on one may expose a memory-ordering bug on
  another (§1.4 → `assembly-fundamentals-and-isas`).

**Formal verification** is real in this niche: **Alive2** for peephole correctness,
**Vale** and **Jasmin** for verified crypto assembly, **HACL\*** and **fiat-crypto** for
verified implementations that *generate* the assembly. If you're writing crypto assembly
by hand in 2026 without a verification story, consider whether you should be.
