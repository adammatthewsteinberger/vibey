---
name: logic-sequential-timing-metastability-cdc-and-hdl
description: "Use for sequential design and the failures that are hardest to debug: latches and flip-flops, timing with setup, hold, slack and metastability, state machine design and encoding, clock domain crossing and the synchronizer patterns that make it safe, HDL and synthesis and what the tool will and will not infer, and test and design for test including scan chains and fault coverage."
---

# Digital Logic and Firmware: Latches and Flip-Flops, Timing and Metastability, State Machines, Clock Domain Crossing, HDL and Synthesis, and Test and DFT

> **Part 3 of 5** of the *CMOS, Logic Gates and Firmware Engineering* reference (plugin `digital-logic-and-firmware-engineering`), covering §14–§19. Sibling skills: `logic-devices-transistors-cmos-gates-and-power` (§0–§8), `logic-standard-cells-boolean-minimization-and-arithmetic` (§9–§13), `logic-firmware-boot-root-of-trust-embedded-practice-and-security` (§20–§25), `logic-reference` (§26–§31). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Boolean algebra and CMOS circuit design do not change. Two things are moving. See §26 → `logic-reference` for the Secure Boot certificate expiry, and open-source firmware and silicon roots of trust.

> **⚠️ SCOPE, because this sits between existing neighbours.** ⚠️ **A semiconductor
> reference covers device physics and fabrication; a microarchitecture reference covers how
> gates become processors. Neither covers the two layers here: HOW TRANSISTORS BECOME
> BOOLEAN LOGIC, and HOW A MACHINE GETS FROM POWER-ON TO AN OPERATING SYSTEM.**
>
> **⚠️ These are the two ends of the stack where the abstractions are built, and where they
> most often leak.**
>
> **⚠️ GOTCHA** boxes mark where the textbook idealization and the real circuit diverge.
>
> **The three ideas that organize this document:**
> 1. **⚠️ CMOS COMPUTES BY CONNECTING, NOT BY AMPLIFYING** (§5 → `logic-devices-transistors-cmos-gates-and-power`). **A static CMOS gate is two
>    complementary switch networks, one connecting the output to power and one to ground,
>    never both. Once you see this, gate construction becomes mechanical and the power
>    behaviour becomes obvious.**
> 2. **⚠️ TIMING IS THE REAL CONSTRAINT, NOT LOGIC** (§15, §17). **Getting the Boolean
>    function right is the easy part. Setup and hold violations, clock skew and metastability
>    are what actually make digital systems fail, and they fail intermittently.**
> 3. **⚠️ TRUST IS A CHAIN THAT STARTS BEFORE ANY SOFTWARE RUNS** (§22 → `logic-firmware-boot-root-of-trust-embedded-practice-and-security`, §25 → `logic-firmware-boot-root-of-trust-embedded-practice-and-security`, §26 → `logic-reference`). **Every
>    security property the OS provides rests on firmware that executed first. Firmware is
>    the most privileged and least examined code in the machine.**

---

## §14. ⚠️ Latches and Flip-Flops

```
⚠️ ⚠️ THE DISTINCTION PEOPLE GET WRONG
   ⚠️ LATCH  ⚠️ LEVEL-sensitive — transparent while enable is
      asserted. Data flows through
   ⚠️ FLIP-FLOP  ⚠️ EDGE-triggered — samples only at the clock
      edge
   ⚠️ "Latch" and "flip-flop" are used loosely in conversation
      and mean genuinely different things in design
⚠️ CONSTRUCTION  ⚠️ cross-coupled inverters for storage · SR
   latch · gated D latch · ⚠️ MASTER-SLAVE (two latches on
   opposite clock phases) = edge-triggered flip-flop
⚠️ ⚠️ INFERRED LATCHES ARE A CLASSIC HDL BUG  ⚠️ an incomplete
   if or case statement in combinational logic makes the
   synthesizer infer a LATCH to hold the unassigned value.
   ⚠️ Almost never intended, causes timing problems, and every
   linter warns about it — heed the warning
⚠️ RESET  ⚠️ synchronous vs asynchronous. ⚠️ Asynchronous reset
   ASSERTION is fine; ⚠️ asynchronous DE-assertion is the
   hazard, because it can violate recovery/removal time —
   hence reset synchronizers
⚠️ ENABLE  ⚠️ use a proper enabled flip-flop, ⚠️ NOT a gated
   clock hand-built from logic (§8's clock gating is done with
   dedicated cells for exactly this reason)
⚠️ REGISTERS, shift registers, counters (⚠️ binary vs GRAY —
   Gray changes one bit at a time, which matters for §17)
```

---

## §15. ⚠️ Timing and Metastability

> **⚠️ §1 → `logic-devices-transistors-cmos-gates-and-power`'s second organizing idea. This is what actually makes digital hardware fail.**
```
⚠️ ⚠️ THE TWO CONSTRAINTS, and they fail differently
   ⚠️ SETUP TIME  data must be stable BEFORE the clock edge.
      ⚠️ Violated by a path being TOO SLOW.
      ⚠️ FIXABLE BY SLOWING THE CLOCK
   ⚠️ HOLD TIME  data must remain stable AFTER the edge.
      ⚠️ Violated by a path being TOO FAST.
      ⚠️ NOT FIXABLE BY SLOWING THE CLOCK — ⚠️ a hold violation
      is a broken chip at any frequency, which is why hold
      failures are far more serious
⚠️ THE PATH EQUATION  ⚠️ clock period ≥ clock-to-Q + logic delay
   + wire delay + setup time − clock skew
⚠️ CLOCK SKEW  ⚠️ arrival time difference between flops.
   ⚠️ It can HELP setup on one path while HURTING hold on
   another — which is why clock tree synthesis targets balance
⚠️ SLACK  ⚠️ the margin. Negative slack = failure. ⚠️ The
   CRITICAL PATH is the worst one, and it sets the frequency
⚠️ ⚠️ METASTABILITY  ⚠️ if setup/hold is violated, the flop can
   enter a state between 0 and 1 and stay there for an
   UNBOUNDED time before resolving randomly
   ⚠️ THERE IS NO CIRCUIT THAT ELIMINATES IT. ⚠️ You can only
   make it ARBITRARILY UNLIKELY by allowing resolution time —
   which is what a two-flop synchronizer buys
   ⚠️ MTBF is the metric, and it improves EXPONENTIALLY with
   the time allowed — which is why adding one more flop stage
   helps so much
```

---

## §16. State Machines

**⚠️ Moore versus Mealy**: ⚠️ **Moore outputs depend only on state (⚠️ registered, glitch
free, one cycle later); Mealy outputs depend on state AND inputs (⚠️ faster response,
combinational path from input to output, which can create timing problems across module
boundaries).**
**⚠️ State encoding**: ⚠️ **binary (fewest flops), ⚠️ ONE-HOT (⚠️ one flop per state,
simpler and faster decode logic, and usually the right choice in FPGAs where flops are
plentiful), and Gray.**
**⚠️ The design discipline**: ⚠️ **state diagram first, then a coded template — and separate
the next-state logic, the state register and the output logic into distinct blocks, because
that structure both reads clearly and synthesizes predictably.**
**⚠️ Unreachable and illegal states** — ⚠️ **and for anything safety-related, a default case
that returns to a known state, because a glitch or upset can put a machine in a state your
diagram doesn't contain.**

---

## §17. ⚠️ Clock Domain Crossing

> **⚠️ Where §15's metastability becomes a design discipline rather than an analysis.**
```
⚠️ THE PROBLEM  ⚠️ a signal generated in one clock domain and
   sampled in another has NO timing relationship. ⚠️ Setup and
   hold WILL be violated eventually — it is a matter of
   probability, not possibility
⚠️ ⚠️ THIS IS THE CLASSIC SOURCE OF "WORKS ON THE BENCH, FAILS
   IN THE FIELD" BUGS. ⚠️ An unsynchronized crossing can run
   correctly for days and then fail
⚠️ THE TECHNIQUES
   ⚠️ TWO-FLOP SYNCHRONIZER  ⚠️ for SINGLE-BIT LEVEL signals only
   ⚠️ PULSE SYNCHRONIZER / toggle synchronizer  for events
   ⚠️ ⚠️ MULTI-BIT DATA CANNOT USE A SIMPLE SYNCHRONIZER —
      ⚠️ each bit resolves independently, so you can capture a
      value that never existed. ⚠️ THIS IS THE MOST DANGEROUS
      CDC MISTAKE
      ⚠️ Use: ⚠️ GRAY CODE (only one bit changes, so a bad
      sample is at worst the old or new value) · ⚠️ handshake ·
      ⚠️ ASYNCHRONOUS FIFO — the standard solution for streams
   ⚠️ RESET SYNCHRONIZATION (§14)
⚠️ ⚠️ CDC VERIFICATION TOOLS EXIST AND SHOULD BE RUN. ⚠️ Static
   CDC analysis finds unsynchronized crossings that simulation
   will not, because simulation does not model metastability
```

---

## §18. HDL and Synthesis

**⚠️ Verilog/SystemVerilog and VHDL** — ⚠️ **and the mental correction that matters most:
⚠️ HDL IS NOT A PROGRAMMING LANGUAGE. It DESCRIBES HARDWARE. ⚠️ Statements are concurrent
by default, and "assignment" creates a wire or a register, not an action in time.**
**⚠️ Blocking versus non-blocking assignment** is the canonical beginner trap:
⚠️ **non-blocking (`<=`) for sequential logic, blocking (`=`) for combinational — and mixing
them in one block produces simulation/synthesis mismatch, where the simulation passes and
the chip doesn't work.**
**⚠️ The synthesizable subset is much smaller than the language** — ⚠️ **delays, most
initial blocks and much of the type system exist for simulation and testbenches only.**
**⚠️ The flow**: ⚠️ **RTL → synthesis to a gate netlist → place and route → static timing
analysis → sign-off** (see a microarchitecture reference §24).
**⚠️ FPGA versus ASIC** targets differ enough to change coding style: ⚠️ **FPGAs have
abundant flops and fixed block RAM and DSP resources; ASICs have a cell library and
enormous NRE.**
**⚠️ Verification is the majority of the effort**: ⚠️ **testbenches, constrained-random,
coverage, assertions (SVA), and formal equivalence checking against §10 → `logic-standard-cells-boolean-minimization-and-arithmetic`'s BDDs.**

---

## §19. Test and DFT

**⚠️ Manufacturing test is not verification** — ⚠️ **verification asks "is the design
right?", test asks "was THIS die made correctly?"**
**⚠️ Fault models**: ⚠️ **stuck-at (the classic), transition/delay faults, bridging — and
ATPG generates patterns against them.**
**⚠️ SCAN CHAINS** are the enabling idea: ⚠️ **connect all flip-flops into a giant shift
register in test mode, so you can load any state and observe any state — converting an
unobservable sequential problem into a tractable combinational one.**
**⚠️ BIST** for memories and logic, ⚠️ **JTAG/boundary scan for board-level test** (see a
peripherals reference §19), ⚠️ **and test compression to keep tester time affordable.**
**⚠️ The cost**: ⚠️ **DFT consumes area and can affect timing, and it is always cheaper than
shipping untestable silicon.**

---

# PART IV — FIRMWARE
