---
name: assembly-fundamentals-and-isas
description: "Use when deciding whether to write assembly at all, learning or comparing instruction sets, or reasoning about what the machine actually does beneath the ISA. Covers the machine model (registers, addressing modes, flags, endianness, alignment, memory ordering), x86-64 (register file, the instruction set honestly, compiler idioms, the x86 tax), AArch64/ARM64, RISC-V (design philosophy, profiles and fragmentation), and other ISAs worth knowing. Includes the router for the whole assembly-programming reference."
---

# Assembly Programming: Fundamentals and ISAs

> **Part 1 of 4** of the *Assembly Programming* reference (plugin `assembly-programming`), covering §0–§5. Sibling skills: `assembly-toolchain-performance-and-simd` (§6–§10), `assembly-systems-crypto-and-inline` (§11–§14), `assembly-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §0. Routing

### 0.1 Should you write assembly at all?

**[DURABLE] For almost all code, no.** Modern compilers beat hand-written assembly on
anything but small, carefully-chosen kernels — and they retarget for free. The legitimate
reasons, in rough order of how often they're actually valid:

| Reason | Notes |
|---|---|
| **Reading compiler output** | The dominant use. Not writing at all |
| **Debugging optimized code / crash dumps** | You have no choice; the source is a fiction at `-O2` |
| **Reverse engineering, malware analysis, security research** | Reading, again |
| **Instructions the compiler won't emit** | Crypto (AES-NI, SHA, carry-less multiply), CRC, special atomics, cache control, hardware-specific instructions |
| **Constant-time cryptography** | §12 → `assembly-systems-crypto-and-inline` — the compiler is actively hostile to your requirements here |
| **Boot code, context switches, interrupt vectors, syscall stubs** | §11 → `assembly-systems-crypto-and-inline` — there is no C for "set up the stack before there is a stack" |
| **Hot kernels after profiling and after intrinsics** | Codecs, BLAS, hashing, parsers. And use **intrinsics first** |
| **Extremely constrained targets** | Tiny MCUs, boot ROMs, size-limited firmware |
| **Compiler bugs / missing optimizations** | Real, but verify before assuming |
| **Learning how machines work** | The best reason of all, and it doesn't need to ship |

**[DURABLE] The ladder, and take it in order:**
```
1. Better algorithm                      ← usually the whole answer
2. Better data layout / memory access    ← usually the rest of it
3. Compiler flags, PGO, LTO
4. Restructure C/C++/Rust so the compiler can vectorize
5. Compiler INTRINSICS                   ← 95% of the benefit, register allocation for free
6. Inline assembly for a specific instruction
7. Hand-written assembly functions
8. Hand-written assembly with microarchitectural scheduling
```
**Steps 5 and 7 are separated by a large maintenance cliff.** Intrinsics keep the
compiler's register allocation, scheduling, and inlining; hand-written assembly does not.

### 0.2 The question router

| Asked about... | Go to |
|---|---|
| Machine model: registers, memory, flags, endianness | §1 |
| x86-64 specifically | §2 |
| AArch64 / ARM64 specifically | §3 |
| RISC-V specifically | §4 |
| Other ISAs (embedded, GPU, historical) | §5 |
| Calling conventions and ABIs | §6 → `assembly-toolchain-performance-and-simd` |
| Assemblers, syntax, toolchain, linking | §7 → `assembly-toolchain-performance-and-simd` |
| Reading disassembly and compiler output | §8 → `assembly-toolchain-performance-and-simd` |
| Performance: pipelines, latency, caches, branches | §9 → `assembly-toolchain-performance-and-simd` |
| SIMD and vector programming | §10 → `assembly-toolchain-performance-and-simd` |
| Systems assembly: interrupts, context switch, boot | §11 → `assembly-systems-crypto-and-inline` |
| Cryptographic and constant-time assembly | §12 → `assembly-systems-crypto-and-inline` |
| Inline assembly and intrinsics | §13 → `assembly-systems-crypto-and-inline` |
| Debugging, testing, verification | §14 → `assembly-systems-crypto-and-inline` |
| "Don't do this" | §15 → `assembly-reference` |
| "Which approach is better?" | §16 → `assembly-reference` (contested) |
| "Is this still current?" | §17 → `assembly-reference` |
| Books, manuals, people | §18 → `assembly-reference` |

---

## §1. The Machine Model

### 1.1 What's actually there

```
┌──────────────────────────────────────────────────────────────┐
│ ARCHITECTURAL STATE (what the ISA promises)                  │
│   general-purpose registers · SIMD/vector registers          │
│   program counter · flags/condition codes · stack pointer    │
│   control/system registers · memory (virtual address space)  │
└──────────────────────────────────────────────────────────────┘
                    ↕  (the ISA is a CONTRACT, not a description)
┌──────────────────────────────────────────────────────────────┐
│ MICROARCHITECTURE (what actually happens)                    │
│   fetch → decode → µop cache → RENAME (physical regs ≫ arch) │
│   → scheduler/reservation stations → OUT-OF-ORDER EXECUTION  │
│   across multiple ports → load/store buffers → RETIRE in     │
│   order · branch predictors · L1/L2/L3 caches · TLBs ·       │
│   prefetchers · store-to-load forwarding · speculation       │
└──────────────────────────────────────────────────────────────┘
```

**[DURABLE] Register renaming is why most naive assembly intuitions fail.** The CPU has
far more physical registers than architectural ones and renames on the fly, so
**write-after-write and write-after-read "dependencies" are free** — only true
read-after-write data dependencies cost you. This is why `xor eax, eax` is faster than
`mov eax, 0` (it's recognized as a zeroing idiom and breaks the dependency chain), and why
"reusing a register to save registers" can be actively harmful.

**[DURABLE] The three things that actually determine speed** (§9 → `assembly-toolchain-performance-and-simd`): the **critical path
through the dependency graph**, **memory access patterns**, and **branch predictability**.
Instruction *count* is a distant fourth and is the thing beginners optimize.

### 1.2 Registers

| Class | Purpose |
|---|---|
| General-purpose | Integers, addresses. x86-64: 16 (32 with APX); AArch64: 31 + zero register; RISC-V: 32 (x0 hardwired to zero) |
| SIMD/vector | Packed data. §10 → `assembly-toolchain-performance-and-simd` |
| Floating-point | Separate on some ISAs, shared with SIMD on others |
| Flags/condition | x86 EFLAGS, ARM NZCV. **RISC-V has none** — a deliberate design choice |
| Special | PC/IP, SP, link register, TLS base, system/control registers |

**[DURABLE] A zero register is a surprisingly large ISA win.** AArch64's `xzr`/`wzr` and
RISC-V's `x0` let one instruction encoding serve many purposes: `add rd, rs, x0` is a move,
`beq rs, x0, label` is branch-if-zero, storing `xzr` is a memset. x86 has no zero register
and needs distinct encodings for all of it.

### 1.3 Addressing modes

```
x86-64:   [base + index*scale + disp]        scale ∈ {1,2,4,8}   — very expressive
          mov rax, [rbx + rcx*8 + 16]
AArch64:  [base], [base, #imm], [base, Xn{, LSL #s}], pre/post-index
          ldr x0, [x1, #16]!        pre-index:  x1 += 16, then load
          ldr x0, [x1], #16         post-index: load, then x1 += 16
RISC-V:   [base + imm12]  ONLY                                   — deliberately minimal
          ld  a0, 16(a1)
```
**[DURABLE] This is the clearest illustration of the CISC/RISC trade-off that survives
into 2026.** x86's addressing modes fold address arithmetic into the load for free —
but they're one reason x86 decoding is hard. RISC-V's single mode means indexed access
costs an extra `add`, which the designers judged a fair price for decode simplicity.
Neither is wrong; they optimize different things.

### 1.4 Endianness, alignment, and memory ordering

- **Endianness**: x86-64, AArch64 (in practice), and RISC-V are all **little-endian**
  today. Big-endian survives in network byte order, some MIPS/PowerPC/SPARC deployments,
  and file formats. **Byte-swap instructions exist**: `bswap`/`movbe` (x86), `rev` (ARM),
  `rev8` (RISC-V Zbb).
- **Alignment**: x86-64 tolerates unaligned scalar access with a small penalty (and
  *requires* alignment for some SIMD instructions and all atomics that must not split a
  cache line). ARM and RISC-V vary — unaligned may fault, may trap-and-emulate slowly, or
  may work fine. **⚠️ A split-cache-line access is dramatically slower everywhere, and a
  split-page access worse still.**
- **Memory ordering [DURABLE, and the most dangerous area in multicore assembly]:**

| ISA | Model |
|---|---|
| **x86-64** | **TSO** (total store order) — strong. Only store→load can reorder. `mfence`/`lock`-prefixed ops for the rest |
| **AArch64** | **Weak**, with acquire/release built into instructions: `ldar`/`stlr`, plus `dmb`/`dsb`/`isb` barriers |
| **RISC-V** | **Weak** (RVWMO), with `fence` and `.aq`/`.rl` suffixes on atomics |
| **POWER** | Weak, notoriously so |

> **⚠️ GOTCHA — x86's strong ordering hides bugs that ARM and RISC-V expose.** Concurrent
> code developed and tested only on x86 routinely breaks on AArch64, because the missing
> barrier never mattered before. This is one of the most common real-world porting
> failures, and it produces rare, load-dependent corruption rather than a clean crash.

---

## §2. x86-64

### 2.1 The register file

```
64-bit   32-bit  16-bit  8-bit    Conventional role (System V AMD64)
rax      eax     ax      al/ah    return value; implicit in mul/div
rbx      ebx     bx      bl       callee-saved
rcx      ecx     cx      cl       4th arg; implicit shift count
rdx      edx     dx      dl       3rd arg; high half of mul/div
rsi      esi     si      sil      2nd arg; string source
rdi      edi     di      dil      1st arg; string destination
rbp      ebp     bp      bpl      frame pointer (callee-saved)
rsp      esp     sp      spl      STACK POINTER — never clobber
r8–r15                            r8/r9 = 5th/6th args; r12–r15 callee-saved
xmm0–15 / ymm0–15 / zmm0–31       SIMD (§10)
rip                               instruction pointer (RIP-relative addressing)
```

> **⚠️ GOTCHA — the 32-bit zero-extension rule.** Writing to a 32-bit register
> **zero-extends into the full 64-bit register**; writing to a 16- or 8-bit register does
> **not** (it merges, creating a **partial-register dependency stall**). So `mov eax, 1`
> clears the upper 32 bits of `rax` — deliberately, and usefully, because it's a shorter
> encoding — while `mov ax, 1` leaves the top 48 bits and creates a false dependency.
> **Prefer 32-bit operations when the value fits**: shorter encoding, and free zeroing.

### 2.2 The instruction set, honestly

x86-64 is **variable-length** (1–15 bytes), **two-operand destructive** (`add rax, rbx`
means `rax += rbx` — APX changes this, §17 → `assembly-reference`), and enormous. Practical groupings:

- **Data movement**: `mov`, `movzx`/`movsx` (zero/sign extend), `lea`, `push`/`pop`,
  `xchg`, `cmov`.
- **`lea` is the workhorse.** It computes an address without accessing memory, so it's a
  free three-operand add-and-shift: `lea rax, [rbx + rcx*4 + 8]`. Compilers use it
  constantly for arithmetic that has nothing to do with addresses.
- **Arithmetic/logic**: `add`/`adc`, `sub`/`sbb`, `imul`/`mul`, `idiv`/`div`
  (**very slow — 20–100 cycles; strength-reduce it**), `and`/`or`/`xor`/`not`, shifts,
  `bt`/`bts`/`btr`.
- **BMI1/BMI2**: `andn`, `bextr`, `blsi`, `tzcnt`, `lzcnt`, `popcnt`, `pdep`/`pext`
  (**note: `pdep`/`pext` are microcoded and glacial on pre-Zen 3 AMD** — a classic
  portability-of-performance trap).
- **Control**: `jmp`, `jcc`, `call`/`ret`, `loop` (**don't** — slower than the equivalent
  `dec`/`jnz` on modern parts).
- **`cmov`** — conditional move, no branch. Essential for §12 → `assembly-systems-crypto-and-inline`, and a good idea whenever a
  branch is unpredictable.
- **Atomics**: `lock`-prefixed RMW, `cmpxchg`, `cmpxchg16b`, `xadd`.
- **Crypto**: AES-NI (`aesenc`…), SHA extensions, `pclmulqdq` (carry-less multiply — the
  basis of fast GCM and CRC).

### 2.3 Idioms you'll see in every compiler's output

```asm
xor  eax, eax        ; rax = 0. Shorter than mov, and BREAKS the dependency chain
test rax, rax        ; set flags from rax without a compare-with-zero
lea  rax, [rbx+rbx*2]; rax = rbx*3, no multiplier, no flags touched
sete al              ; materialize a condition as 0/1 without branching
cdq / cqo            ; sign-extend eax→edx:eax before idiv  (forgetting this is a classic bug)
endbr64              ; CET indirect-branch landing pad — required at indirect targets
```

### 2.4 The x86 tax

**[DURABLE]** Variable-length decoding is genuinely expensive, which is why modern x86
cores have **µop caches** to bypass the decoder on hot loops. Practical consequences:
- **Code density matters more than instruction count** on x86 — fitting a loop in the µop
  cache or in fewer 32-byte fetch windows is a real optimization.
- **Alignment of branch targets** to 16 or 32 bytes can matter.
- The **legacy modes** (real, protected, long) and the accumulated 40 years of encodings
  are the reason a full x86 assembler is a large program.

---

## §3. AArch64 (ARM64)

### 3.1 The register file

```
x0–x30    64-bit GPRs;  w0–w30 are the 32-bit views (writing wN zero-extends to xN)
  x0–x7   arguments and return values
  x8      indirect result location / Linux syscall number
  x9–x15  caller-saved (temporary)
  x16,x17 IP0/IP1 — intra-procedure-call scratch, may be clobbered by the LINKER's veneers
  x18     PLATFORM REGISTER — reserved on some OSes (⚠️ Darwin, Windows). Don't touch
  x19–x28 callee-saved
  x29     FP (frame pointer)
  x30     LR (link register — the return address)
sp        stack pointer  (⚠️ MUST be 16-byte aligned at any public interface)
xzr/wzr   the ZERO REGISTER (reads 0, writes discarded) — encoding 31, context-dependent with sp
pc        not directly writable
v0–v31    128-bit SIMD (NEON), also used as scalar FP (s/d/h views)
z0–z31    SVE scalable vectors; p0–p15 predicates (§10)
```

### 3.2 The character of the ISA

**Fixed 32-bit instructions**, load/store architecture (**arithmetic never touches memory**),
mostly three-operand and non-destructive, and a genuinely clean encoding.

```asm
; the canonical prologue/epilogue
stp  x29, x30, [sp, #-16]!   ; push FP and LR, pre-decrement sp
mov  x29, sp
; ...
ldp  x29, x30, [sp], #16     ; pop, post-increment
ret                          ; branch to x30

; conditional execution without branches
cmp   x0, x1
csel  x2, x3, x4, lt         ; x2 = (x0 < x1) ? x3 : x4    ← constant-time friendly
cinc  x2, x2, ne             ; conditional increment
cbz   x0, label              ; compare-and-branch-if-zero: one instruction, no flags
tbz   x0, #3, label          ; test-bit-and-branch

; loading a 64-bit constant takes up to four instructions
movz x0, #0x1234, lsl #48
movk x0, #0x5678, lsl #32    ; movk = move-keep (doesn't clear other bits)
; ...or, far more often:
adrp x0, symbol              ; PC-relative page address (±4 GB)
add  x0, x0, :lo12:symbol    ; plus the low 12 bits
```

**[DURABLE] The `adrp`/`add` pair is the single most characteristic AArch64 idiom** and
the thing that confuses people coming from x86's RIP-relative addressing. AArch64 can't
encode a 64-bit address in a 32-bit instruction, so PC-relative addressing is split into
a 4 KB-page-granular part and a 12-bit offset.

**Pointer authentication (PAC) and BTI** — Armv8.3+/8.5+ security features you'll see in
modern compiler output: `paciasp`/`autiasp` sign and authenticate the return address in
the prologue/epilogue (defeating ROP), and `bti c` marks legal indirect-branch targets.
**Don't strip these**; on Apple platforms they're mandatory.

**Atomics**: the classic **LL/SC** pair `ldxr`/`stxr` (load-exclusive / store-exclusive,
with a retry loop), plus the much better **LSE** atomics from Armv8.1 (`ldadd`, `swp`,
`cas`) which are single instructions and scale far better under contention.

---

## §4. RISC-V

### 4.1 The design philosophy, and why it matters to you

**[DURABLE] RISC-V is a small base plus modular extensions**, which makes it the easiest
major ISA to learn and the most annoying to target portably.

```
RV32I / RV64I   base integer (I = 32 registers; E = 16, for embedded)
M  multiply/divide      A  atomics          F/D/Q  float (single/double/quad)
C  compressed (16-bit)  V  vector (§10)     B  bit manipulation (Zba/Zbb/Zbs)
Zicsr control regs      Zifencei            Zk*  scalar crypto     Zvk*  vector crypto
```
The shorthand: **RV64GC** = IMAFD + Zicsr + Zifencei + C, the general-purpose target.

```
x0/zero  hardwired zero     x1/ra  return address     x2/sp  stack pointer
x3/gp    global pointer     x4/tp  thread pointer     x5–7/t0–2  temporaries
x8/s0/fp saved / frame ptr  x9/s1  saved
x10–17/a0–a7  arguments and return values      x18–27/s2–11  saved
x28–31/t3–6   temporaries
```

**Notably absent: condition flags.** Comparison and branch are fused into one instruction
(`beq`, `bne`, `blt`, `bge`, `bltu`, `bgeu`), and `slt`/`sltu` materialize a comparison as
0/1. This removes a serialization point and a rename hazard that x86 and ARM both carry.

```asm
addi sp, sp, -16
sd   ra, 8(sp)
sd   s0, 0(sp)
# ...
ld   ra, 8(sp)
ld   s0, 0(sp)
addi sp, sp, 16
ret                  # pseudo-instruction for: jalr x0, 0(ra)
```

**⚠️ Pseudo-instructions are pervasive and you must know they're not real**: `li`, `la`,
`mv`, `nop`, `ret`, `call`, `j`, `beqz`, `not`, `neg`. The assembler expands each into one
or more real instructions, and `li` with a large constant becomes `lui`+`addi`.

### 4.2 Profiles — the fragmentation fix

**[VERSIONED]** The extension modularity created a real portability problem, and
**profiles** are the answer: a named set of mandatory and optional extensions that
software can target.

**RVA23 was ratified 21 October 2024** and is the current 64-bit application-processor
profile. What matters for assembly programmers:
- **The V (vector) extension is now MANDATORY** — it was optional in RVA22. Vectors are no
  longer an optional accelerator; they're a baseline capability software can assume.
- **RVA23 is the baseline requirement for the Android RISC-V ABI.**
- Also newly mandatory in RVA23U64: **Zvfhmin** (vector half-precision), **Zvbb** (vector
  bit manipulation), **Zvkt** (vector data-independent execution latency — see §12 → `assembly-systems-crypto-and-inline`),
  **Zihintntl**, **Zicond** (integer conditional ops), **Zimop**/**Zcmop**, **Zcb**,
  **Zfa**, and **Supm** (pointer masking).
- **The scalar crypto extensions Zkn and Zks are no longer options** — the stated goal is
  for hardware and software vendors to **move to vector crypto**, since vectors are now
  mandatory and vector crypto is substantially faster.
- The hypervisor extension is in the S-mode profile.
- Ratified specs are **frozen**: "No changes are allowed… Ratified extensions are never
  revised." Changes go into new extensions.

---

## §5. Other ISAs Worth Knowing

| ISA | Where you'll meet it |
|---|---|
| **ARM32 / Thumb-2** | Older embedded, Cortex-M. Thumb-2's mixed 16/32-bit encoding is excellent for code density; **Cortex-M is Thumb-only** |
| **AVR** | Arduino, 8-bit MCUs. Harvard architecture — separate code and data address spaces, which surprises everyone |
| **MSP430, PIC, 8051** | Deeply embedded, still shipping in volume |
| **POWER / PowerPC** | IBM servers, older consoles. Weak memory model, big-endian heritage |
| **MIPS** | Networking silicon, older Roku/embedded, and **every undergraduate architecture course** |
| **SPARC** | Register windows — a genuinely different idea worth understanding |
| **s390x** | IBM mainframe. Big-endian, and still absolutely everywhere in banking |
| **WebAssembly** | A stack machine and a compile target, not hardware. Structured control flow, no registers |
| **x86 16/32-bit** | Boot code, BIOS/UEFI, DOS-era reverse engineering, retro |
| **GPU ISAs** (PTX/SASS, RDNA, SPIR-V) | Mostly generated; PTX is a virtual ISA, SASS is the real one |
| **6502, Z80, 68000** | Retro computing and demoscene, and the best teaching ISAs ever made |
