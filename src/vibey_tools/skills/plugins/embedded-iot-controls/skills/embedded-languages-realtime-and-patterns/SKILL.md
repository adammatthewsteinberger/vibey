---
name: embedded-languages-realtime-and-patterns
description: "Use when writing firmware and deciding how to write it: C and its traps, the safe C++ subset, where Rust in embedded actually stands, real-time taxonomy and critical sections, atomics and memory barriers, the concurrency bug taxonomy, and the working set of firmware patterns — layered architecture, state machines, the lock-free SPSC ring buffer, memory pools instead of malloc, rollover-safe time handling, driver patterns, ISR-to-task handoff, error handling and fault forensics, the supervised watchdog, and the anti-pattern catalogue."
---

# Embedded & IoT: Languages, Real-Time Correctness, and Design Patterns

> **Part 2 of 5** of the *Embedded Systems & IoT Controls — Deep Technical Reference* reference (plugin `embedded-iot-controls`), covering §3–§5. Sibling skills: `embedded-silicon-and-firmware-models` (§0–§2), `embedded-industrial-control-connectivity-and-cloud` (§6–§9), `embedded-security-safety-and-testing` (§10–§13), `embedded-reference` (§14–§19). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §17 → `embedded-reference` for the currency snapshot and what goes stale first.

> **How to read this.** This is a reference, not a tutorial. Sections are independent.
> Three markers appear throughout:
> - **[UNIVERSAL]** — physics, math, or architecture. True regardless of vendor. Trust it.
> - **[VENDOR]** — specific to a chip, SDK, or toolchain. Verify against the datasheet/errata.
> - **[CONTESTED]** — competent engineers disagree. Both cases are presented. Do not pick a side on the reader's behalf.
>
> **⚠️ GOTCHA** boxes mark the failure modes that actually burn people. They are the
> highest-value content in this document.

---

## §3. Languages

### 3.1 The honest comparison

| | C | C++ (subset) | Rust | MicroPython | Ada/SPARK |
|---|---|---|---|---|---|
| Smallest viable target | ~2 KB | ~4 KB | ~4 KB | ~256 KB | ~8 KB |
| Memory safety | none | partial (RAII) | **compile-time** | runtime (GC) | strong + provable |
| Certified toolchain | many | many | **Ferrocene** | none | many |
| Ecosystem breadth | vast (vendor) | vast | good & growing | modest | narrow |
| Hiring pool | huge | large | small but growing | large | tiny |
| Determinism | full | full (w/o exceptions/heap) | full | **no (GC pauses)** | full |
| Best for | anything, esp. legacy & certified | large firmware needing abstraction | new safety/security-critical work | prototyping, education, non-RT | highest-integrity |

### 3.2 C — the lingua franca, and its traps

**Fixed-width types always.** `#include <stdint.h>`; `int` is 16-bit on some targets and
32-bit on others.

**Integer promotion is the #1 silent C bug in embedded code:**
```c
uint8_t  a = 200, b = 100;
uint8_t  c = a + b;              /* a,b promoted to int; 300 truncated to 44 */
uint16_t x = 0xFFFF;
uint32_t y = x << 16;            /* x promoted to int(32); if int is 16-bit → UB */
if (some_uint8 << 8 > 1000) ...  /* promotion + precedence trap */
```
Rule: cast explicitly at every point where width matters. `(uint32_t)x << 16`.

**Signed overflow is undefined behaviour**, and modern compilers exploit it aggressively
(`if (x + 1 < x)` gets optimized to `false`). Unsigned overflow is defined (wraps). Use
unsigned for counters and rely on it deliberately (§5.5).

**`volatile` means "the compiler must not cache or reorder *this* access."** It does
**not** mean atomic, and it does **not** create a memory barrier for other accesses.
Every memory-mapped register must be `volatile` (CMSIS headers do this). Every variable
shared between an ISR and a task must be `volatile` **and** accessed atomically (§4.3).
Using `volatile` as a substitute for a lock is a bug that works until it doesn't.

**Strict aliasing**: accessing an object through a pointer of an incompatible type is UB.
The classic float↔uint32 bit-punning via pointer cast is UB; use `memcpy` (the compiler
optimizes it away) or a `union` (well-defined in C, implementation-defined in C++).

**MISRA C** — current version is **MISRA C:2025** (published March 2025), an incremental
update to **MISRA C:2023** (April 2023), which itself consolidated MISRA C:2012 plus
Amendments 1–4 and TC2. Coverage is C90/C99/C11/C18; roughly 225 active guidelines.
Amendment 4's Rules 22.11–22.20 added **concurrency and atomics guidance** — the first
formal MISRA coverage of multi-threaded C, which matters now that multicore MCUs are
common. **MISRA C++:2023** (October 2023) targets C++17, defines ~179 rules, and **merged
AUTOSAR C++14 into MISRA** — so "AUTOSAR C++14" as a separate standard is effectively
superseded. A new MISRA C++ is in development with no announced date.

Practical MISRA advice: **adopt it as a static-analysis ruleset with documented deviations,
not as gospel.** The deviation process is part of the standard. Teams that treat every
rule as mandatory produce worse code (e.g. banning all `goto` when the single-exit
cleanup `goto` pattern is clearer than nested flags).

**Useful C idioms in embedded:**
```c
/* X-macros: one list, many derived artifacts — no drift between table and enum */
#define SENSOR_LIST(X)            \
    X(TEMP,   0x01, temp_read)    \
    X(HUMID,  0x02, humid_read)   \
    X(PRESS,  0x04, press_read)

typedef enum { 
#define X(name, mask, fn) SENSOR_##name,
    SENSOR_LIST(X)
#undef X
    SENSOR_COUNT
} sensor_id_t;

static const sensor_desc_t sensors[SENSOR_COUNT] = {
#define X(name, mask, fn) [SENSOR_##name] = { .mask = (mask), .read = (fn) },
    SENSOR_LIST(X)
#undef X
};

/* Compile-time assertions — catch layout/config errors at build, not at 3am */
_Static_assert(sizeof(protocol_frame_t) == 16, "frame packing changed");
_Static_assert((TICK_HZ % CONTROL_HZ) == 0,    "control rate must divide tick rate");
```

### 3.3 C++ in embedded — the safe subset

**Zero-cost and worth using:**
- `constexpr` / `consteval` — move computation to compile time (CRC tables, lookup tables,
  unit conversions). This is C++'s single biggest embedded win.
- `enum class` — no implicit int conversion, no namespace pollution.
- `std::array<T,N>` — same layout as a C array, with `.size()` and bounds-checked `.at()`.
- **RAII** — deterministic cleanup for locks, DMA channels, chip-select assertions. Reduces
  a whole class of "forgot to release" bugs to zero.
- Templates for **static polymorphism** (CRTP) — dispatch resolved at compile time, no
  vtable, fully inlinable.
- **Strong types** — `struct Millivolts { int32_t v; };` prevents the unit-mixing errors
  that destroyed the Mars Climate Orbiter.
- `[[nodiscard]]` on every function returning an error code.

**Costly / banned in most embedded shops:**
- **Exceptions** — table-based unwinding costs flash even unused (link `-fno-exceptions`),
  and throw/catch timing is unbounded. Nearly universally disabled.
- **RTTI / `dynamic_cast`** — `-fno-rtti`.
- **`iostream`** — pulls in tens of KB. Use `printf`, or better, a binary logger (§12.5 → `embedded-security-safety-and-testing`).
- **Heap-based STL** (`std::vector`, `std::string`, `std::function`, `std::map`) — dynamic
  allocation and unbounded latency. Use **ETL (Embedded Template Library)** for
  fixed-capacity equivalents, or `etl::delegate`/function-pointer for callbacks.

**Standard build flags for embedded C++:**
`-fno-exceptions -fno-rtti -fno-threadsafe-statics -fno-use-cxa-atexit`
(the last two remove hidden guards/registration on static locals and destructors).

```cpp
/* CRTP static polymorphism — polymorphic interface, zero vtable, fully inlined */
template <typename Impl>
class SensorBase {
public:
    int32_t read() { return static_cast<Impl*>(this)->read_impl(); }
};

class Bme280 : public SensorBase<Bme280> {
    friend class SensorBase<Bme280>;
    int32_t read_impl() { /* register access */ return 0; }
};

/* Compile-time-safe register access — wrong-width writes fail to compile */
template <uintptr_t Addr, typename T = uint32_t>
struct Reg {
    static T  read()          { return *reinterpret_cast<volatile T*>(Addr); }
    static void write(T v)    { *reinterpret_cast<volatile T*>(Addr) = v; }
    static void set(T mask)   { write(read() |  mask); }
    static void clear(T mask) { write(read() & ~mask); }
};
```

### 3.4 Rust in embedded — where it actually stands in 2026

**The ecosystem is no longer experimental.** Key facts as of 2026:
- **`embedded-hal` 1.0 is released and stable**, giving the driver ecosystem a
  semver-stable trait foundation (both blocking and async variants). Hundreds of
  platform-agnostic sensor/peripheral driver crates build on it.
- **Embassy** is the de-facto async runtime, with first-party HALs for STM32 (all
  families), nRF (52/53/54/91), RP2040/RP235x, TI MSPM0, NXP MCX-A, plus `esp-hal` and
  `ch32-hal` from their respective communities. Embassy compiles on **stable Rust** since
  1.75.
- **RTIC** remains the choice when you want a pure execution framework with
  compile-time-verified resource locking (Stack Resource Policy) and no runtime.
- **`probe-rs`** has effectively displaced OpenOCD for Rust workflows (and works fine for
  C too); **`defmt`** gives deferred, format-string-interned logging that is dramatically
  cheaper than `printf`.
- **Espressif has elevated `esp-rs` to a top-tier official SDK** for its RISC-V line.
- **Ferrocene** (Ferrous Systems) is the qualified toolchain: **TÜV SÜD-qualified for
  ISO 26262 ASIL D, IEC 61508 SIL 3 (supporting customer efforts to SIL 4), and IEC 62304
  Class C**, with a **certified subset of `core` at IEC 61508 SIL 2 / ISO 26262 ASIL B**
  (a critical 2025–26 milestone, since `no_std` Rust is unusable without `core`). Targets
  include Linux, QNX Neutrino, and bare-metal Armv8-A and **Armv7E-M**.

**The layering** (learn these four words, they explain everything):
```
PAC   — Peripheral Access Crate. Auto-generated from the vendor SVD by svd2rust.
        Raw registers, but type-safe field access. e.g. stm32f4
HAL   — Hardware Abstraction Layer. Ergonomic drivers implementing embedded-hal traits.
        e.g. stm32f4xx-hal, embassy-stm32, esp-hal
BSP   — Board Support Package. Named pins/peripherals for a specific board.
Driver— Platform-agnostic device crate, generic over embedded-hal traits.
```

**The typestate pattern** — Rust's genuinely novel embedded contribution. Peripheral
configuration is encoded in the *type*, so misuse fails at compile time:
```rust
// A pin configured as Input cannot be written to — this is a compile error, not a bug.
let gpioa = dp.GPIOA.split();
let mut led   = gpioa.pa5.into_push_pull_output();   // Pin<'A',5, Output<PushPull>>
let     button = gpioa.pa0.into_pull_up_input();     // Pin<'A',0, Input<PullUp>>

led.set_high().unwrap();
// button.set_high();  // ← does not compile: no such method on an Input pin

// Ownership prevents two drivers silently sharing a peripheral:
let spi = Spi::new(dp.SPI1, (sck, miso, mosi), MODE_0, 1.MHz(), &clocks);
let display = Display::new(spi, dc_pin, cs_pin);      // spi is MOVED
// let other = OtherDriver::new(spi);  // ← does not compile: spi already moved
```
```rust
// Embassy: concurrency without thread stacks. Each task is a state machine
// sized at compile time; no per-task stack allocation.
#[embassy_executor::task]
async fn blinker(mut led: Output<'static>, interval: Duration) {
    loop {
        led.toggle();
        Timer::after(interval).await;     // yields; zero CPU while waiting
    }
}

#[embassy_executor::main]
async fn main(spawner: Spawner) {
    let p = embassy_stm32::init(Default::default());
    let led = Output::new(p.PA5, Level::Low, Speed::Low);
    spawner.spawn(blinker(led, Duration::from_millis(500))).unwrap();
    // Other tasks run cooperatively on the same executor.
    // Multiple executors at different interrupt priorities give you preemption.
}
```

**[CONTESTED] Rust vs C for new embedded work.** Steelman both:
- *For Rust*: memory-safety bugs (buffer overflow, use-after-free, data race) are
  eliminated by construction — and these are the dominant CVE class in firmware.
  The typestate/ownership model catches whole categories of driver misuse at compile time.
  `cargo` dependency management beats copying vendor SDK zips. `defmt`+`probe-rs` is a
  better debug loop than most C toolchains. Ferrocene removes the "we can't certify it"
  objection.
- *For C*: the vendor ecosystem is C — every reference design, app note, errata
  workaround, silicon vendor driver, and third-party stack. Rust HAL coverage for a
  specific obscure part is often incomplete, and you end up writing `unsafe` PAC code
  anyway. Certified C toolchains, MISRA tooling, and static analyzers are mature and
  procurable. Your team already knows C, and hiring embedded Rust engineers is hard.
  Async Rust in safety contexts raises unresolved questions about qualifying the runtime.
- *The pragmatic middle*: Rust for new greenfield connected/security-sensitive products on
  well-supported parts (nRF, STM32, RP2350, ESP32-C/P); C for legacy, obscure silicon,
  and anything where the vendor stack is load-bearing. Mixed-language via FFI is normal.

### 3.5 Everything else

- **MicroPython / CircuitPython**: excellent for prototyping, teaching, and non-real-time
  glue on parts with ≥256 KB flash. **Not** for control loops (GC pauses are
  unbounded-ish) or for products needing sub-ms determinism. CircuitPython's driver library
  breadth is a genuine prototyping accelerator.
- **TinyGo**: LLVM-based Go for MCUs. Nice concurrency model; GC still present (though
  configurable); ecosystem thinner than Rust's.
- **Ada/SPARK**: the highest-assurance option. SPARK's provable absence of runtime errors
  is used in avionics and rail. Tiny talent pool; superb where it fits.
- **WebAssembly on MCUs** (WAMR, Wasm3, WASI): sandboxed, updatable application logic on
  top of native firmware. Real production use in edge/plugin architectures; costs
  interpretation overhead unless AOT-compiled.
- **Elixir/Nerves**: Linux-class devices where BEAM's supervision trees and hot-code
  loading suit long-lived fleet devices.
- **Lua (eLua/NodeMCU), JavaScript (Espruino, Moddable XS)**: scripting layers for
  configurable behaviour, useful when end users need to customize device logic.

---

## §4. Concurrency, Timing, and Real-Time Correctness

### 4.1 Real-time taxonomy [UNIVERSAL]

- **Hard real-time**: a missed deadline is a **system failure**. Airbag deployment, motor
  commutation, safety interlocks. Requires provable WCET and a scheduler you can analyze.
- **Firm real-time**: a late result is **useless** but not catastrophic. Video frame,
  sensor sample in a fusion window.
- **Soft real-time**: a late result **degrades quality**. UI responsiveness, telemetry
  upload.

**"Real-time" does not mean "fast."** A system that responds in 10 ms *always* is
real-time; one that responds in 100 µs *usually* and 50 ms *occasionally* is not.
Determinism is the property; speed is incidental.

**WCET (worst-case execution time)** is genuinely hard on modern parts: caches, branch
prediction, DMA bus contention, and flash wait states all make measured-average wildly
optimistic. Approaches, in order of rigour:
1. **Static WCET analysis** (aiT, Bound-T) — sound but expensive and needs a processor
   model.
2. **Measurement-based with instrumentation** — GPIO toggle at entry/exit, capture with a
   scope or logic analyzer; run pathological inputs deliberately.
3. **Cycle counters** — `DWT->CYCCNT` on Cortex-M3+ gives you free cycle-accurate timing.
4. **Add margin.** Typical practice: design to ≤50–70% CPU utilization so that measurement
   error and future features don't eat your margin.

```c
/* DWT cycle counter — the cheapest accurate profiler on Cortex-M3+ */
static inline void cyccnt_enable(void) {
    CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
    DWT->CYCCNT = 0;
    DWT->CTRL  |= DWT_CTRL_CYCCNTENA_Msk;
}
#define CYCCNT_START()  uint32_t _t0 = DWT->CYCCNT
#define CYCCNT_ELAPSED() (DWT->CYCCNT - _t0)   /* unsigned: wrap-safe */
```

### 4.2 Critical sections — the cost you keep paying

```c
/* Coarse: disables ALL interrupts including the 10 kHz control loop. */
__disable_irq();
shared_state.a = x;
shared_state.b = y;
__enable_irq();

/* Better on Cortex-M: BASEPRI masks only interrupts at/below a priority.
   Your highest-priority "kernel-transparent" ISRs keep running. */
static inline uint32_t critical_enter(void) {
    uint32_t prev = __get_BASEPRI();
    __set_BASEPRI(CRITICAL_PRIORITY << (8 - __NVIC_PRIO_BITS));
    __DMB();
    return prev;
}
static inline void critical_exit(uint32_t prev) {
    __DMB();
    __set_BASEPRI(prev);
}
```
**⚠️ GOTCHA — nesting.** `__enable_irq()` unconditionally enables. If a critical section
nests inside another, the inner exit re-enables interrupts early. **Always save and
restore** the previous mask (as above), never blind enable/disable.

**[UNIVERSAL] The best critical section is the one you don't take.** Prefer:
lock-free SPSC structures (§5.3), atomic single-word updates, double-buffering, and
message passing over shared mutable state.

### 4.3 Atomics and memory barriers

- On a single-core Cortex-M, **aligned 32-bit loads and stores are atomic**. A `uint32_t`
  written by an ISR and read by a task needs no lock — but does need `volatile` (or
  `atomic_load_explicit`) so the compiler doesn't cache it.
- **Read-modify-write is NOT atomic.** `counter++` is load/add/store; an ISR between the
  load and store loses the increment. Use `LDREX/STREX` (via `atomic_fetch_add` or
  `__atomic_*` builtins), or a critical section.
- **`volatile` provides no ordering guarantees between different variables** and no
  hardware barrier. On Cortex-M's mostly-in-order, non-speculative memory model you often
  get away with it; on Cortex-A, multicore, or with a write buffer in front of a
  peripheral, you do not.
- Barriers: `__DMB()` (data memory barrier — orders memory accesses), `__DSB()` (data
  synchronization barrier — waits for completion), `__ISB()` (instruction sync — flushes
  the pipeline; required after changing the vector table, MPU config, or when
  self-modifying).
- **The canonical pattern**: after writing a register that changes execution behaviour
  (MPU enable, VTOR, NVIC disable before a critical operation), issue `__DSB(); __ISB();`.

```c
/* Correct ISR→task flag with C11 atomics */
#include <stdatomic.h>
static atomic_bool  data_ready = false;
static uint8_t      buffer[N];             /* only ISR writes before flag set */

void DMA_IRQHandler(void) {
    /* ... DMA filled buffer ... */
    atomic_store_explicit(&data_ready, true, memory_order_release);  /* publishes buffer */
}

void task(void) {
    if (atomic_load_explicit(&data_ready, memory_order_acquire)) {   /* acquires buffer */
        process(buffer);
        atomic_store_explicit(&data_ready, false, memory_order_relaxed);
    }
}
```
Release/acquire is what makes the buffer contents visible — a plain `volatile bool` does
not guarantee that on an out-of-order or write-buffered machine.

### 4.4 The concurrency bug taxonomy

| Bug | Signature | Fix |
|---|---|---|
| **Race condition** | Works on debug build, fails at -O2 or under load | Atomics, locks, single-writer discipline |
| **Priority inversion** | High-priority task misses deadline sporadically | Priority inheritance mutexes |
| **Deadlock** | System hangs, watchdog fires | Lock ordering discipline; never take two locks; timeouts on every take |
| **Livelock** | 100% CPU, no progress | Backoff; check retry loops |
| **Lost wakeup** | Task sleeps forever despite event | Check-then-wait must be atomic; use notification counters not flags |
| **Torn read** | Multi-word value (64-bit timestamp, struct) partially updated | Double-buffer, seqlock, or critical section |
| **ABA** | Lock-free structure corrupts | Tagged pointers / generation counters |
| **Stack overflow** | Corruption of an unrelated variable | MPU guard + high-water marks |

> **⚠️ GOTCHA — the 64-bit timestamp tear.** A 32-bit MCU cannot atomically read a 64-bit
> microsecond counter maintained by an ISR. Reading `hi` then `lo` can straddle a
> rollover. Use the **seqlock** pattern: reader reads a sequence counter, reads the data,
> re-reads the counter, retries if it changed or is odd.

---

## §5. Design Patterns — the working set

### 5.1 Layered architecture, and why it matters for testing

```
┌─────────────────────────────────────────────┐
│ Application  — business logic, state machines│  ← 100% host-testable
├─────────────────────────────────────────────┤
│ Services     — logging, config, comms, OTA   │  ← host-testable w/ fakes
├─────────────────────────────────────────────┤
│ Device drivers — sensor.c, motor.c, radio.c  │  ← testable against a fake bus
├─────────────────────────────────────────────┤
│ HAL / BSP    — i2c_write(), gpio_set()       │  ← the seam. ONE header per bus.
├─────────────────────────────────────────────┤
│ Vendor SDK / registers                       │  ← target only
└─────────────────────────────────────────────┘
```
**[UNIVERSAL] The single highest-leverage architectural decision in firmware is putting a
narrow, dependency-injected seam between drivers and hardware.** Everything above the seam
becomes unit-testable on a host machine, in a CI pipeline, in milliseconds. Teams that do
this find bugs 100× faster than teams that only test on hardware.

```c
/* The seam: an interface struct, not a global function. Enables fakes. */
typedef struct i2c_bus {
    int (*write)(void *ctx, uint8_t addr, const uint8_t *d, size_t n);
    int (*read )(void *ctx, uint8_t addr,       uint8_t *d, size_t n);
    void *ctx;
} i2c_bus_t;

/* Driver depends on the interface, never on the vendor HAL. */
typedef struct { const i2c_bus_t *bus; uint8_t addr; } bme280_t;

int bme280_read_temp(bme280_t *dev, int32_t *out_millideg) {
    uint8_t reg = 0xFA, raw[3];
    int rc = dev->bus->write(dev->bus->ctx, dev->addr, &reg, 1);
    if (rc != 0) return rc;
    rc = dev->bus->read(dev->bus->ctx, dev->addr, raw, sizeof raw);
    if (rc != 0) return rc;
    *out_millideg = bme280_compensate(raw);   /* pure function — trivially testable */
    return 0;
}
```
No heap, no globals, no vtable cost beyond one indirect call, and `bme280_compensate` can
be tested against the datasheet's reference values without any hardware at all.

### 5.2 State machines — pick the right form

| Form | Best when | Cost |
|---|---|---|
| `switch` on enum | ≤5 states, few events | Simplest; degrades badly with growth |
| **State table** (2-D array of handlers) | Many states × events, uniform | Data-driven, compact, easy to audit/verify |
| Function-pointer state | States have distinct entry/exit behaviour | Idiomatic C; O(1) dispatch |
| **Hierarchical (HSM/statechart)** | Shared behaviour across states, "cancel from any state" | Miro Samek's QP; eliminates duplicated transitions |
| Generated (Zephyr SMF, Yakindu, Stateflow) | Formal spec exists / cert required | Traceability; tool lock-in |

```c
/* State table — the workhorse. Adding a state or event is a table edit, not surgery. */
typedef enum { ST_IDLE, ST_ARMING, ST_RUNNING, ST_FAULT, ST_COUNT } state_t;
typedef enum { EV_START, EV_STOP, EV_TICK, EV_FAULT, EV_COUNT } event_t;

typedef state_t (*handler_t)(void *ctx);
static state_t on_idle_start(void *c);   /* ... */

static const handler_t fsm[ST_COUNT][EV_COUNT] = {
    /*             EV_START        EV_STOP        EV_TICK        EV_FAULT   */
    [ST_IDLE]    = { on_idle_start,  NULL,          NULL,          on_fault   },
    [ST_ARMING]  = { NULL,           on_abort,      on_arm_tick,   on_fault   },
    [ST_RUNNING] = { NULL,           on_stop,       on_run_tick,   on_fault   },
    [ST_FAULT]   = { NULL,           on_fault_ack,  NULL,          NULL       },
};

void fsm_dispatch(fsm_ctx_t *ctx, event_t ev) {
    handler_t h = fsm[ctx->state][ev];
    if (h == NULL) { log_unhandled(ctx->state, ev); return; }  /* explicit, not silent */
    state_t next = h(ctx);
    if (next != ctx->state) {
        state_exit(ctx, ctx->state);      /* run-to-completion: exit, then entry */
        ctx->state = next;
        state_entry(ctx, next);
    }
}
```
**[UNIVERSAL] Run-to-completion semantics**: an event is processed fully before the next
is dequeued. This is what makes statecharts analyzable. Never process an event from inside
a state handler — post it to the queue instead.

**Active Object pattern** (Samek's QP, and the model behind Zephyr's message queues): each
component is a state machine + an event queue + a thread; components communicate only by
posting events. No shared mutable state → no mutexes → no priority inversion → no
deadlocks. This is the strongest general architecture for medium-to-large firmware and is
worth reading *Practical UML Statecharts in C/C++* for.

### 5.3 Lock-free SPSC ring buffer — the one you'll write a hundred times

```c
/* Single-producer (ISR) / single-consumer (task). No locks. Capacity must be a
   power of two. Uses the full range of the index type and lets it WRAP —
   this is why unsigned overflow being well-defined matters. */
typedef struct {
    uint8_t  buf[RB_SIZE];             /* RB_SIZE must be a power of 2 */
    volatile uint32_t head;            /* written ONLY by producer */
    volatile uint32_t tail;            /* written ONLY by consumer */
} ringbuf_t;

_Static_assert((RB_SIZE & (RB_SIZE - 1)) == 0, "RB_SIZE must be a power of two");

static inline uint32_t rb_count(const ringbuf_t *r) { return r->head - r->tail; }
static inline bool     rb_full (const ringbuf_t *r) { return rb_count(r) == RB_SIZE; }
static inline bool     rb_empty(const ringbuf_t *r) { return r->head == r->tail; }

/* Producer side — call from ISR only */
bool rb_push(ringbuf_t *r, uint8_t v) {
    if (rb_full(r)) return false;                    /* drop, or overwrite: choose deliberately */
    r->buf[r->head & (RB_SIZE - 1)] = v;
    __DMB();                                         /* data visible BEFORE index advance */
    r->head++;                                       /* single word, atomic on 32-bit */
    return true;
}

/* Consumer side — call from task only */
bool rb_pop(ringbuf_t *r, uint8_t *out) {
    if (rb_empty(r)) return false;
    *out = r->buf[r->tail & (RB_SIZE - 1)];
    __DMB();                                         /* read data BEFORE releasing slot */
    r->tail++;
    return true;
}
```
**Why it's correct**: exactly one writer per index; the power-of-two mask makes wraparound
free; the difference `head - tail` is correct across rollover because unsigned arithmetic
wraps. **Why it breaks**: two producers, or two consumers, or a non-power-of-two size, or
omitting the barriers on a machine with a write buffer.

**⚠️ GOTCHA — the "one slot wasted" alternative.** Many textbook ring buffers compare
`(head+1)%N == tail` to detect full, wasting a slot. The counting version above uses the
whole buffer but requires that the index type is wide enough that `head - tail` can never
legitimately exceed the buffer size — which it can't, since we never push when full.

### 5.4 Memory pools instead of malloc

```c
/* Fixed-block allocator: O(1), no fragmentation, deterministic. */
typedef struct block { struct block *next; } block_t;

typedef struct {
    block_t *free_list;
    uint8_t *storage;
    size_t   block_size, count;
} pool_t;

void pool_init(pool_t *p, void *mem, size_t block_size, size_t count) {
    p->storage = mem; p->block_size = block_size; p->count = count;
    p->free_list = NULL;
    for (size_t i = 0; i < count; i++) {                  /* thread the free list */
        block_t *b = (block_t *)(p->storage + i * block_size);
        b->next = p->free_list;
        p->free_list = b;
    }
}
void *pool_alloc(pool_t *p) {
    uint32_t s = critical_enter();
    block_t *b = p->free_list;
    if (b) p->free_list = b->next;
    critical_exit(s);
    return b;                                             /* NULL if exhausted — CHECK IT */
}
void pool_free(pool_t *p, void *blk) {
    uint32_t s = critical_enter();
    ((block_t *)blk)->next = p->free_list;
    p->free_list = blk;
    critical_exit(s);
}
```
Pattern: one pool per message size class, sized at design time from the worst-case
in-flight count. Exhaustion is then a *design* question you answer before shipping, not a
runtime surprise.

### 5.5 Time handling — rollover-safe, always

```c
/* WRONG: breaks every 49.7 days on a 32-bit ms counter, and immediately if the
   deadline computation wraps. This bug ships constantly. */
if (millis() > deadline) { ... }

/* RIGHT: signed difference. Works across rollover for intervals < 2^31 ms (~24 days). */
static inline bool time_after(uint32_t a, uint32_t b) {
    return (int32_t)(a - b) > 0;
}
if (time_after(millis(), deadline)) { ... }

/* Elapsed time — always subtract, never compare absolutes */
uint32_t start = millis();
/* ... */
uint32_t elapsed = millis() - start;   /* correct across wrap */
```
**[UNIVERSAL] Rules of embedded time:**
1. Use a **monotonic** counter for intervals; never wall-clock (it jumps on NTP/RTC sync).
2. Always compute **differences**, never compare absolute timestamps.
3. Know your counter width and pick an interval type that can't exceed half of it.
4. `k_uptime_get()` (Zephyr, 64-bit) and `esp_timer_get_time()` (64-bit µs) sidestep the
   problem — use 64-bit where available.

**Debouncing** — two correct approaches:
```c
/* 1. Integrator (noise-immune, no fixed delay): sample at fixed rate */
static uint8_t integrator = 0;
#define DEBOUNCE_MAX 10
bool debounce_sample(bool raw) {
    if (raw && integrator < DEBOUNCE_MAX) integrator++;
    else if (!raw && integrator > 0)      integrator--;
    if (integrator == 0)            return false;   /* stable low  */
    if (integrator == DEBOUNCE_MAX) return true;    /* stable high */
    return last_stable;                             /* hysteresis zone */
}

/* 2. Shift register (fast, 1 line): N consecutive identical samples */
static uint16_t hist = 0;
bool debounce_shift(bool raw) {
    hist = (uint16_t)((hist << 1) | (raw ? 1u : 0u));
    if ((hist & 0x00FF) == 0x00FF) return true;
    if ((hist & 0x00FF) == 0x0000) return false;
    return last_stable;
}
```
Never `delay(50)` in a button handler. Never poll a button in a busy loop.

### 5.6 Driver patterns

**Blocking → non-blocking → interrupt → DMA** is a progression, and the API shape should
reflect where you are:
```c
/* Blocking: fine for init-time, fatal in a control loop */
int spi_transfer(const uint8_t *tx, uint8_t *rx, size_t n);

/* Non-blocking with completion callback: the general-purpose shape */
typedef void (*xfer_done_t)(void *ctx, int status);
int spi_transfer_async(const uint8_t *tx, uint8_t *rx, size_t n,
                       xfer_done_t cb, void *ctx);

/* Callback runs in ISR context → it must only signal, never process.
   This is the ISR→task handoff (5.7). */
```

**Bus arbitration**: when multiple tasks share an SPI/I²C bus, own the bus with a **mutex**
held for the duration of a *transaction* (CS assert → transfer → CS deassert), not per
byte. Wrap it in RAII (C++) or a `bus_lock()/bus_unlock()` pair with a timeout, and treat
timeout as a hard error worth logging, not a retry-forever.

**Double-buffered / ping-pong DMA** — the pattern for continuous acquisition:
```
DMA circular mode with half-transfer + transfer-complete interrupts:
  HT  interrupt → process first half   while DMA fills second half
  TC  interrupt → process second half  while DMA fills first half
No gaps, no missed samples, CPU touched only twice per buffer.
```
**⚠️ GOTCHA (M7)**: invalidate the D-cache for the half you're about to read (§1.2 → `embedded-silicon-and-firmware-models`).

### 5.7 ISR-to-task handoff — the canonical FreeRTOS form

```c
/* Highest-value 20 lines in an RTOS codebase. Get this shape right everywhere. */
static TaskHandle_t s_worker;                  /* set at task creation */

void UART_IRQHandler(void) {
    BaseType_t higher_woken = pdFALSE;

    if (UART->ISR & UART_ISR_RXNE) {
        uint8_t b = (uint8_t)UART->RDR;        /* read clears the flag on most parts */
        (void)rb_push(&rx_ring, b);            /* lock-free; ISR is sole producer */

        /* Notify, don't process. Notification is faster than a semaphore. */
        vTaskNotifyGiveFromISR(s_worker, &higher_woken);
    }
    if (UART->ISR & UART_ISR_ORE) {            /* overrun: count it, don't ignore it */
        UART->ICR = UART_ICR_ORECF;
        s_diag.uart_overruns++;
    }

    /* If we woke a task of higher priority than the interrupted one,
       request a context switch on ISR exit — otherwise latency is one tick. */
    portYIELD_FROM_ISR(higher_woken);
}

void worker_task(void *arg) {
    for (;;) {
        /* Block until notified; the count tells us how many notifications we missed. */
        (void)ulTaskNotifyTake(pdTRUE, portMAX_DELAY);
        uint8_t b;
        while (rb_pop(&rx_ring, &b)) {
            protocol_feed(b);                  /* all real work happens here */
        }
    }
}
```
**Three things people get wrong**: forgetting `portYIELD_FROM_ISR` (adds up to one tick of
latency), calling a non-`FromISR` API from an ISR (corrupts the kernel), and running the
ISR at a priority above `configMAX_SYSCALL_INTERRUPT_PRIORITY` while calling kernel APIs
(silent, intermittent corruption — see §1.1 → `embedded-silicon-and-firmware-models` gotcha).

### 5.8 Error handling and fault forensics

**[UNIVERSAL] The three-tier model:**
1. **Expected, recoverable** → return an error code. Every caller checks it.
   `[[nodiscard]]`/`__attribute__((warn_unused_result))` makes ignoring it a warning.
2. **Programmer error / impossible state** → `assert`. In development, halt and inspect.
   In production, **do not silently compile it out** — record it and reset (a controlled
   reset with a logged reason beats undefined behaviour).
3. **Hardware fault** → fault handler that captures state and resets.

```c
/* Production assert: record, then reset. Never NDEBUG your asserts away silently. */
void assert_failed(const char *file, uint32_t line) {
    __disable_irq();
    s_crash.magic = CRASH_MAGIC;                 /* in .noinit — survives soft reset */
    s_crash.kind  = CRASH_ASSERT;
    s_crash.line  = line;
    strncpy(s_crash.file, file, sizeof s_crash.file - 1);
    /* flush to backup RAM / RTC domain if available */
    NVIC_SystemReset();
}
```

**HardFault handler that actually tells you something** — this is worth its weight in gold:
```c
/* Naked wrapper: figure out which stack was in use, pass the frame to C. */
__attribute__((naked)) void HardFault_Handler(void) {
    __asm volatile (
        "tst   lr, #4          \n"   /* EXC_RETURN bit 2: 0=MSP, 1=PSP */
        "ite   eq              \n"
        "mrseq r0, msp         \n"
        "mrsne r0, psp         \n"
        "mov   r1, lr          \n"
        "b     hardfault_c     \n"
    );
}

typedef struct {           /* the hardware-stacked exception frame */
    uint32_t r0, r1, r2, r3, r12, lr, pc, psr;
} exc_frame_t;

void hardfault_c(exc_frame_t *frame, uint32_t exc_return) {
    s_crash.magic = CRASH_MAGIC;
    s_crash.kind  = CRASH_HARDFAULT;
    s_crash.pc    = frame->pc;       /* ← the faulting instruction. Look it up in the .map */
    s_crash.lr    = frame->lr;       /* ← the caller */
    s_crash.psr   = frame->psr;
    s_crash.cfsr  = SCB->CFSR;       /* Configurable Fault Status: which fault, precisely */
    s_crash.hfsr  = SCB->HFSR;       /* HardFault Status (FORCED bit ⇒ escalated) */
    s_crash.mmfar = SCB->MMFAR;      /* MemManage Fault Address — valid if CFSR.MMARVALID */
    s_crash.bfar  = SCB->BFAR;       /* BusFault Address     — valid if CFSR.BFARVALID   */
    s_crash.exc_return = exc_return;
    /* Optionally: walk the stack for plausible return addresses to build a backtrace. */
    NVIC_SystemReset();
}
```
**Decoding CFSR** (the bits you'll actually see):
- `IACCVIOL` — instruction fetch from a non-executable region → jumped through a bad
  function pointer.
- `PRECISERR` + valid `BFAR` — dereferenced a bad address; BFAR tells you which.
- `IMPRECISERR` — a buffered write faulted later; disable write buffering
  (`SCB->ACTLR |= DISDEFWBUF`) during debug to make it precise.
- `UNALIGNED` — unaligned access with `UNALIGN_TRP` enabled, or an unaligned `LDM/STM`.
- `UNDEFINSTR` — executed garbage, or called an FPU instruction with the FPU disabled.
  **The FPU one is extremely common**: enabling `-mfpu=fpv4-sp-d16` without enabling
  CP10/CP11 in `CPACR` faults on the first float operation.
- `STKERR`/`UNSTKERR` — stack overflow during exception entry/exit.

**Enable the specific fault handlers.** By default, MemManage/BusFault/UsageFault escalate
to HardFault, losing information. Set `SCB->SHCSR |= MEMFAULTENA | BUSFAULTENA |
USGFAULTENA` at boot so you get the precise handler and a meaningful `HFSR.FORCED == 0`.

### 5.9 The supervised watchdog

```c
/* Each critical task registers and periodically checks in. A single supervisor
   verifies ALL tasks are alive within their deadlines before kicking the IWDG. */
typedef struct { uint32_t last_ms; uint32_t deadline_ms; const char *name; } wdt_client_t;
static wdt_client_t clients[WDT_MAX_CLIENTS];
static uint32_t     registered_mask;
static volatile uint32_t checkin_mask;

void wdt_checkin(uint8_t id) {
    clients[id].last_ms = millis();
    __atomic_or_fetch(&checkin_mask, 1u << id, __ATOMIC_RELAXED);
}

void wdt_supervisor_tick(void) {              /* run at, say, 10 Hz */
    uint32_t now = millis();
    for (uint8_t i = 0; i < WDT_MAX_CLIENTS; i++) {
        if (!(registered_mask & (1u << i))) continue;
        if ((uint32_t)(now - clients[i].last_ms) > clients[i].deadline_ms) {
            s_crash.kind = CRASH_WDT_STARVED;
            strncpy(s_crash.file, clients[i].name, sizeof s_crash.file - 1);
            return;                            /* DO NOT kick — let the IWDG fire */
        }
    }
    IWDG->KR = 0xAAAA;                         /* all healthy: kick */
}
```
This turns "the system hung" into "task `comms` missed its 500 ms deadline" in your fleet
telemetry.

### 5.10 The anti-pattern catalogue

| Anti-pattern | Why it's bad | Do instead |
|---|---|---|
| `delay()`/`HAL_Delay()` in production logic | Burns CPU, blocks everything, destroys real-time | Non-blocking timers, RTOS `vTaskDelay`, state machines |
| Work inside an ISR | Latency, priority inversion, unbounded jitter | Signal + defer to task |
| `malloc`/`free` at runtime | Fragmentation, non-determinism, silent OOM | Static allocation or fixed pools |
| Global variables everywhere | Untestable, racy, unfollowable data flow | Context structs passed explicitly |
| Ignoring return codes | Failures propagate silently, corrupt state | `[[nodiscard]]`, check every one |
| Magic numbers | Unmaintainable; unit errors | Named constants w/ units in the name (`TIMEOUT_MS`) |
| Copy-pasted drivers | Bug fixed in one copy, not the other four | One driver, parameterized |
| `while(!(REG & FLAG));` with no timeout | Infinite hang on hardware fault | Bounded wait + error return |
| Busy-wait polling | Burns power, blocks | Interrupt or `__WFI()` |
| Kicking watchdog from a timer ISR | Proves nothing; masks hangs | Supervised watchdog (§5.9) |
| One giant `main.c` | Untestable, unreviewable | Layered modules (§5.1) |
| Floating-point in an ISR without FPU context save | Corrupts task FP state | Enable lazy stacking, or keep FP out of ISRs |
| Unbounded recursion | Stack overflow, unanalyzable | Iteration; MISRA bans recursion outright |
| Testing only on hardware | Slow loop, poor coverage, no CI | Host tests + fakes (§12 → `embedded-security-safety-and-testing`) |
