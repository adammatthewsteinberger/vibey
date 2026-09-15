---
name: embedded-industrial-control-connectivity-and-cloud
description: "Use when working on OT/industrial control or connected-device systems: the PLC scan cycle, IEC 61131-3 languages, fieldbus and industrial protocols (Modbus, PROFINET, EtherCAT), OPC UA vs MQTT/Sparkplug and the unified namespace, Purdue/ISA-95 and the IT/OT boundary, TSN; PID done correctly, beyond PID, and motor control; choosing a radio, BLE, Thread and Matter, LoRaWAN, cellular, the application protocols (MQTT, CoAP), edge computing and TinyML; and the cloud, fleet, and lifecycle layer — the platform landscape, identity and provisioning, OTA update, and fleet observability."
---

# Embedded & IoT: Industrial Control, Control Theory, Connectivity, and Fleet Lifecycle

> **Part 3 of 5** of the *Embedded Systems & IoT Controls — Deep Technical Reference* reference (plugin `embedded-iot-controls`), covering §6–§9. Sibling skills: `embedded-silicon-and-firmware-models` (§0–§2), `embedded-languages-realtime-and-patterns` (§3–§5), `embedded-security-safety-and-testing` (§10–§13), `embedded-reference` (§14–§19). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §6. Industrial Control and OT

### 6.1 The PLC scan cycle [UNIVERSAL]

```
┌──> 1. INPUT SCAN     — snapshot ALL physical inputs into the input image table
│    2. PROGRAM EXEC   — logic runs against the SNAPSHOT, writes to output image
│    3. OUTPUT SCAN    — write output image to physical outputs, atomically
│    4. HOUSEKEEPING   — comms, diagnostics, watchdog
└────┘  repeat; scan time typically 1–50 ms
```
**Why the image tables matter**: within one scan, an input cannot change. This gives
deterministic, race-free logic and is the reason ladder logic is safely writable by people
who are not software engineers. It also means **your effective input latency is up to 2
scan times**, and that a fast physical event shorter than one scan is *invisible* unless
you use a high-speed counter or interrupt-driven I/O module.

**Scan-time discipline**: the scan watchdog trips if a scan exceeds its limit. Long `FOR`
loops, blocking communications, and unbounded string operations in Structured Text are the
usual culprits.

### 6.2 IEC 61131-3 languages

| Language | Form | Best for | Notes |
|---|---|---|---|
| **LD** Ladder Diagram | Relay-logic rungs | Discrete/interlock logic, plant-maintainable | Universal in North America |
| **FBD** Function Block Diagram | Wired blocks | Signal flow, process control, analog chains | Dominant in process industry |
| **ST** Structured Text | Pascal-like text | Math, algorithms, loops, string handling | Where real software engineering happens |
| **SFC** Sequential Function Chart | Steps + transitions | Batch, sequence, start/stop procedures | Maps to Grafcet; great for sequences |
| **IL** Instruction List | Assembly-like | — | **Deprecated in IEC 61131-3 3rd edition** |

**IEC 61499** is the distributed-control successor (event-driven function blocks across
devices), academically influential, commercially niche. **PLCopen** publishes the
motion-control function block standard (`MC_MoveAbsolute`, `MC_Power`, …) and the safety
function block set — these matter because they make motion code portable across vendors.

**Structured Text idioms worth knowing:**
```pascal
(* Edge detection — R_TRIG/F_TRIG are standard function blocks *)
VAR
    rStart   : R_TRIG;
    tonDelay : TON;
END_VAR

rStart(CLK := xStartButton);
IF rStart.Q THEN                      (* rising edge only, once per press *)
    eState := STARTING;
END_IF

(* Timers are function block INSTANCES with state — never re-declare inside a loop *)
tonDelay(IN := (eState = STARTING), PT := T#3S);
IF tonDelay.Q THEN
    eState := RUNNING;
END_IF
```
> **⚠️ GOTCHA — retentive vs non-retentive variables.** `VAR RETAIN` survives a warm
> restart; `VAR PERSISTENT` survives a cold restart/download (vendor semantics vary!).
> Getting this wrong means a machine restarts mid-cycle in an unsafe state after a power
> blip. It is one of the most consequential and least-documented distinctions in PLC work.

### 6.3 Fieldbus and industrial protocols

| Protocol | Layer | Determinism | Typical cycle | Notes |
|---|---|---|---|---|
| **Modbus RTU** | RS-485 serial | poll-only | 10–100 ms | Trivial, ubiquitous, no security, no timestamps |
| **Modbus TCP** | Ethernet | poll-only | 5–50 ms | Same data model over TCP/502 |
| **PROFIBUS DP** | RS-485 | token/master-slave | 1–10 ms | Legacy but enormous installed base |
| **PROFINET RT / IRT** | Ethernet | RT: soft; IRT: hard (µs) | 1–10 ms / <1 ms | Siemens-dominant |
| **EtherNet/IP (CIP)** | Ethernet | implicit I/O w/ RPI | 1–10 ms | Rockwell-dominant |
| **EtherCAT** | Ethernet (special) | **hard, <100 µs, jitter <1 µs** | 50 µs–1 ms | Frame processed **on the fly** by each slave; distributed clocks |
| **CANopen** | CAN | event + sync | 1–10 ms | Object dictionary, PDO/SDO, NMT state machine |
| **IO-Link** | Point-to-point 3-wire | ~2.3 ms cycle | — | Sensor-level; carries parameters + diagnostics, not just a signal |
| **BACnet** | IP/MSTP | none | seconds | Building automation |
| **DNP3 / IEC 61850** | IP/serial | GOOSE: <4 ms | — | Utilities/substation; 61850 GOOSE is multicast, safety-relevant |
| **OPC UA** | TCP/HTTPS/MQTT | not RT (except over TSN) | 50 ms+ | **Information model**, security, discovery |

**EtherCAT's trick, because it explains why it's fast**: the master sends one frame that
travels the ring; each slave reads its output data and writes its input data **into the
passing frame in hardware** as it goes by, with ~1 µs of propagation delay per node. There
is no per-node packet, no switching latency, and no software stack in the loop.
Distributed Clocks then synchronize all nodes to <1 µs, which is what makes coordinated
multi-axis motion possible.

**Modbus register model — the endianness trap [VENDOR chaos, UNIVERSAL pain]:**
```
Data model (all 16-bit addressed, 0-based on the wire, 1-based in docs — the classic
off-by-one):
  Coils              (FC 01 read / 05,15 write)   1-bit  R/W   4x0001-style: 0xxxx
  Discrete Inputs    (FC 02 read)                 1-bit  R     1xxxx
  Input Registers    (FC 04 read)                16-bit  R     3xxxx
  Holding Registers  (FC 03 read / 06,16 write)  16-bit  R/W   4xxxx

A 32-bit float spans TWO registers. There is NO standard for the order. In the wild:
  ABCD  big-endian           (most common, "big-endian word, big-endian byte")
  CDAB  big-endian byte swap ("word-swapped" — extremely common on legacy drives)
  BADC  little-endian byte swap
  DCBA  little-endian
```
**⚠️ GOTCHA:** if a value reads as a plausible-but-wrong number (e.g. 3.6e-38 instead of
25.4), you have a word-order mismatch. Always make word order a *configuration* item in
your Modbus client, never a hard-coded assumption. Document your device's choice in the
register map and publish it — the vendors who don't are the reason integrators hate them.

**A register map convention that saves integrators' lives:**
```
| Addr | Type | Fmt   | Access | Scale | Unit  | Name              | Notes                |
|------|------|-------|--------|-------|-------|-------------------|----------------------|
| 4001 | u16  | -     | R      | 1     | -     | device_id         | 0x1234 constant      |
| 4002 | u16  | -     | R      | 1     | -     | fw_version        | BCD major.minor      |
| 4010 | i32  | ABCD  | R      | 0.001 | °C    | temperature       | -40..125             |
| 4012 | f32  | ABCD  | R      | 1     | kPa   | pressure          | NaN = sensor fault   |
| 4100 | u16  | bits  | R/W    | 1     | -     | control_word      | b0=run, b1=reset     |
| 4200 | u16  | -     | R      | 1     | -     | fault_code        | see appendix         |
```
Publish the scale, the unit, the invalid-value sentinel, and the word format for every
point. That table is the actual product for anyone integrating your device.

### 6.4 OPC UA vs MQTT/Sparkplug — the live architectural debate

**[CONTESTED]** and the most consequential IIoT architecture question right now.

- **OPC UA** is an *information model* first: address space, typed nodes, methods,
  historical access, alarms & conditions, built-in security (X.509, signing, encryption),
  and **companion specifications** that standardize semantics per industry (machine tools,
  robotics, pumps, packaging). Client/server is the mature, widely-implemented mode.
  **OPC UA PubSub (Part 14)** exists in the spec but adoption remains limited relative to
  client/server as of 2026; treat claims of ubiquitous PubSub with scepticism.
- **MQTT** is a *transport*: publish/subscribe, tiny, offline-tolerant, brokered, with no
  opinion whatsoever about payload or topic structure. That freedom becomes topic-tree
  chaos at scale.
- **Sparkplug B** layers the missing OT semantics onto MQTT: a mandated topic namespace
  `spBv1.0/{group}/{msg_type}/{edge_node}/{device}`, Protobuf payloads with typed metrics
  and timestamps, and **birth/death certificates** (NBIRTH/DBIRTH announce the full metric
  set; NDEATH via MQTT Last Will marks a node offline) giving stateful,
  report-by-exception operation without polling.
- **The mainstream 2026 architecture** is not either/or: **OPC UA at the machine (the PLC
  exposes companion-spec-modelled data) → edge gateway translates → MQTT/Sparkplug B to a
  broker → Unified Namespace consumed by MES, historian, analytics, and cloud.** OPC UA
  supplies meaning; MQTT supplies distribution.
- **Sparkplug's real trade-off**: it deliberately forgoes MQTT retained messages and uses
  QoS 0 for DDATA in favour of deterministic state via birth/death. That is a *feature*
  for OT state management and a *limitation* if you need guaranteed delivery of every
  sample. Know which you need.

**Unified Namespace (UNS)** is the architectural idea that there should be exactly one
real-time, hierarchically-organized, event-driven source of truth for the whole
enterprise's current state — typically an MQTT broker with an ISA-95-shaped topic tree
(`enterprise/site/area/line/cell/...`) — that every system publishes to and subscribes
from, replacing point-to-point integrations. It is genuinely transformative when done
well and a mess when the topic namespace isn't designed up front by one owner.

### 6.5 Purdue model / ISA-95 and the IT/OT boundary

```
Level 5  Enterprise (ERP)                        ─┐
Level 4  Site business planning (MES/ERP edge)    │ IT
─────────────────────── DMZ ──────────────────────┤ ← the boundary that matters
Level 3  Site operations (historian, MES, OPC)   ─┤
Level 2  Supervisory (SCADA, HMI)                 │ OT
Level 1  Control (PLC, DCS, safety PLC)           │
Level 0  Process (sensors, actuators)            ─┘
```
**[UNIVERSAL] OT inverts the CIA triad.** IT prioritizes Confidentiality → Integrity →
Availability. OT prioritizes **Safety → Availability → Integrity → Confidentiality**. A
control that "fails secure" by locking out an operator during a process upset can turn a
deviation into an incident. This single inversion explains most IT/OT friction.

**Practical boundary controls**: an industrial DMZ with no direct L3→L4 protocol
traversal, replicated historians rather than direct database access, **unidirectional
gateways / data diodes** where the risk justifies it, and jump hosts with session
recording for vendor access. Colonial Pipeline is the reference lesson on why the *billing
side* being compromised can stop the *operational* side (§16 → `embedded-reference`).

### 6.6 Time-Sensitive Networking (TSN)

Standard Ethernet is non-deterministic (queuing, bursts). TSN is a set of IEEE 802.1
amendments that make it deterministic while keeping standard hardware:
- **802.1AS** — generalized PTP time synchronization (sub-µs across the network).
- **802.1Qbv** — time-aware shaper: gated transmission windows per traffic class. This is
  the core scheduling mechanism.
- **802.1Qbu / 802.3br** — frame preemption: a high-priority frame interrupts a
  best-effort frame mid-transmission.
- **802.1Qci** — per-stream filtering and policing (protects against a babbling node).
- **802.1CB** — frame replication and elimination for reliability (seamless redundancy).

**OPC UA over TSN** is the "converged network" vision: one Ethernet infrastructure
carrying deterministic control traffic and IT traffic. Real, deployed in automotive and
some machine builders; still expensive and integration-heavy for general industry.

---

## §7. Control Theory as Practiced in Firmware

### 7.1 PID done correctly

Textbook PID is three lines. Production PID is thirty, and the extra twenty-seven are
where the engineering lives.

```c
typedef struct {
    float kp, ki, kd;
    float dt;              /* FIXED sample period, seconds — see note below */
    float integral;
    float prev_meas;       /* derivative on MEASUREMENT, not error */
    float d_filt;          /* filtered derivative state */
    float tau;             /* derivative low-pass time constant, seconds */
    float out_min, out_max;
    bool  first_run;
} pid_t;

float pid_update(pid_t *p, float setpoint, float meas) {
    float error = setpoint - meas;

    /* ---- Proportional ---- */
    float P = p->kp * error;

    /* ---- Derivative on measurement (kills SETPOINT KICK) ----
       d/dt(error) spikes to infinity on a setpoint step. d/dt(measurement) does not.
       Sign flips because d(sp - meas)/dt = -d(meas)/dt for constant sp.            */
    if (p->first_run) { p->prev_meas = meas; p->d_filt = 0.0f; p->first_run = false; }
    float raw_d = -(meas - p->prev_meas) / p->dt;
    p->prev_meas = meas;

    /* ---- Filter the derivative (MANDATORY on any real sensor) ----
       Unfiltered D amplifies sensor noise by kd/dt. First-order LPF: */
    float alpha = p->dt / (p->tau + p->dt);
    p->d_filt  += alpha * (raw_d - p->d_filt);
    float D = p->kd * p->d_filt;

    /* ---- Integral with CONDITIONAL INTEGRATION anti-windup ----
       Compute the unsaturated output first; only integrate if we are not saturated
       in the direction that would make saturation worse.                          */
    float I_candidate = p->integral + p->ki * error * p->dt;
    float u_unsat     = P + I_candidate + D;

    bool saturating_high = (u_unsat > p->out_max) && (error > 0.0f);
    bool saturating_low  = (u_unsat < p->out_min) && (error < 0.0f);
    if (!saturating_high && !saturating_low) {
        p->integral = I_candidate;             /* only then commit */
    }

    float u = P + p->integral + D;

    /* ---- Saturate ---- */
    if (u > p->out_max) u = p->out_max;
    if (u < p->out_min) u = p->out_min;
    return u;
}

/* Bumpless transfer: when switching manual→auto, back-calculate the integral so the
   output does not jump. */
void pid_set_auto(pid_t *p, float current_output, float setpoint, float meas) {
    p->integral  = current_output - p->kp * (setpoint - meas);
    p->prev_meas = meas;
    p->d_filt    = 0.0f;
    p->first_run = false;
}
```

**The five PID mistakes that cause ~90% of field problems:**
1. **No anti-windup** — integrator charges while the actuator is saturated; the system
   massively overshoots when it comes off the limit. This is the #1 issue.
2. **Derivative on error** — setpoint changes produce a huge output spike ("derivative
   kick").
3. **Unfiltered derivative** — sensor noise × kd/dt drives the actuator into chatter.
4. **Variable `dt`** — computing `dt` from a timestamp each call means gain varies with
   jitter. Run the loop from a **hardware timer interrupt at a fixed rate** and treat `dt`
   as a constant. If you must handle variable dt, the math still works but tuning becomes
   unreliable.
5. **Sample rate too slow** — rule of thumb: sample at **10–20× the closed-loop bandwidth**
   you want. A 1 Hz process needs ≥10 Hz sampling; a current loop at 1 kHz bandwidth needs
   10–20 kHz.

**Tuning methods, ranked by practicality:**
- **Lambda / IMC tuning** — pick a desired closed-loop time constant λ; compute gains from
  a first-order-plus-dead-time (FOPDT) model. Predictable, conservative, the process
  industry default.
- **Relay autotuning (Åström–Hägglund)** — drive the process with a relay, measure the
  resulting limit cycle to find the ultimate gain and period, then apply tuning rules. The
  basis of most "autotune" buttons.
- **Cohen–Coon** — better than Ziegler–Nichols for dead-time-dominant processes.
- **Ziegler–Nichols** — historically important, **aggressively underdamped** (~25%
  overshoot by design). Use as a starting point, then detune. Don't ship Z-N gains.
- **Manual**: increase Kp until sustained oscillation, back off to ~half; add Ki to remove
  steady-state error; add Kd last and only if you have a clean sensor.

**Fixed-point vs float**: on any Cortex-M4F/M7/M33 with an FPU, use `float`. Single-
precision add/mul is 1–3 cycles. On M0/M0+ without an FPU, software float is 50–100+
cycles and Q15/Q31 fixed-point (with CMSIS-DSP) is the right answer — but watch overflow
and be explicit about your scaling.

### 7.2 Beyond PID

- **Cascade control**: inner fast loop (e.g. motor current, 10 kHz) inside an outer slow
  loop (position, 1 kHz) inside an outer-outer (temperature, 1 Hz). Each loop should be
  **5–10× faster** than the one enclosing it. This is how nearly all real motion and
  process control is structured, and it solves problems that no amount of single-loop
  tuning will.
- **Feedforward**: if you know the disturbance or the required steady-state effort, add it
  directly. Feedback then only corrects the error. In motion control, velocity and
  acceleration feedforward reduce following error by an order of magnitude.
- **Dead time / transport delay**: PID degrades badly when dead time approaches the
  process time constant. **Smith predictor** uses a process model to control against a
  delay-free prediction. Fragile to model error; use with care.
- **State-space + observers**: for MIMO or when states aren't directly measurable. A
  **Luenberger observer** estimates unmeasured states; a **Kalman filter** does it
  optimally under Gaussian noise assumptions.
- **Complementary filter**: the poor man's Kalman for IMU fusion, and often the right
  choice on an M0: `angle = a*(angle + gyro*dt) + (1-a)*accel_angle`. Two lines, no matrix
  math, and it captures the essential idea (trust the gyro short-term, the accelerometer
  long-term).
- **MPC at the edge**: real on Cortex-M7/M33-class hardware for small problems (embedded
  QP solvers like OSQP/qpOASES). Worth it when constraints matter (thermal limits,
  actuator limits) and a model exists.

### 7.3 Motor control

**Commutation methods** in order of complexity:
1. **Six-step / trapezoidal** (BLDC): switch phases based on Hall sensors. Simple, torque
   ripple at commutation, adequate for fans/pumps.
2. **Sinusoidal**: smoother, still no current regulation in the rotating frame.
3. **FOC (Field-Oriented Control)**: the standard for anything requiring precision.

**FOC in one paragraph**: measure two phase currents → **Clarke transform** (3-phase abc →
2-axis stationary αβ) → **Park transform** (αβ → rotating dq frame, using rotor angle) →
now torque-producing current `iq` and flux-producing current `id` are **DC quantities**,
so two simple PI loops regulate them → **inverse Park** → **Space Vector Modulation**
(SVPWM, ~15% better DC bus utilization than sinusoidal PWM) → three PWM duty cycles.

**Timing is everything**: the current loop runs at the PWM frequency (typically 10–20 kHz)
and must complete within one PWM period. ADC sampling must be synchronized to the PWM —
sample at the **centre of the PWM period** (when the low-side FETs are on and the current
is at its average), triggered by the timer, not by software.

**Rotor angle sources**: Hall sensors (60° resolution, cheap), incremental encoder
(needs indexing), absolute encoder/resolver (expensive, no homing), or **sensorless**
(back-EMF observer or high-frequency injection) — sensorless is free in BOM and expensive
in engineering, and has a low-speed blind spot.

> **⚠️ GOTCHA — dead time and its compensation.** Hardware dead time prevents
> shoot-through, but it distorts the output voltage (the actual volt-seconds don't match
> the commanded duty), producing torque ripple and current distortion at low speed. Dead-
> time compensation (adding a sign-of-current-dependent correction to the duty) is standard
> practice in production FOC and absent from most tutorials.

---

## §8. Connectivity

### 8.1 Choosing a radio — the decision table

| Tech | Range | Data rate | Power | Topology | Infra needed | Best for |
|---|---|---|---|---|---|---|
| **BLE** | 10–100 m | 0.125–2 Mbps | very low | star / mesh | phone or gateway | Wearables, sensors, commissioning, local UI |
| **Thread** | 10–30 m/hop, mesh | 250 kbps | low | **mesh, IPv6** | border router | Home/building sensors; Matter's preferred transport |
| **Zigbee** | similar | 250 kbps | low | mesh | coordinator | Legacy lighting/building; Zigbee 4.0 recently released |
| **Wi-Fi (2.4/5)** | 30–100 m | 10s–100s Mbps | **high** | star | AP | Mains-powered, high bandwidth, camera |
| **Wi-Fi HaLow (802.11ah)** | ~1 km | 150 kbps–8 Mbps | medium | star | AP | Sub-GHz IP, long range, moderate rate |
| **LoRaWAN** | 2–15 km | 0.3–50 kbps | **very low** | star-of-stars | gateway + network server | Utility metering, agriculture, private LPWAN |
| **NB-IoT** | cellular | ~30–100 kbps | very low | cellular | carrier | Deep-indoor static meters — **but check carrier support** |
| **LTE-M (Cat-M1)** | cellular | ~300 kbps–1 Mbps | low | cellular | carrier | Mobile assets, voice-capable, best roaming |
| **LTE Cat-1 / Cat-1bis** | cellular | ~10 Mbps | medium | cellular | carrier | The safe global default in 2026 |
| **5G RedCap / eRedCap** | cellular | 10s Mbps | medium | cellular (SA) | carrier | Mid-tier 5G; ~30 operators in 21 countries as of early 2026 |
| **UWB** | 10–50 m | — | medium | — | anchors | Centimetre ranging, secure access |
| **Satellite NTN** | global | very low | medium | — | constellation | Remote assets; store-and-forward with small constellations |

**Cellular reality check for 2026:**
- **2G and 3G are sunset in most markets**; devices still on them need a migration path.
- **NB-IoT has been a commercial underperformer outside China** and carrier support is
  uneven — **AT&T shut down its NB-IoT network**; T-Mobile and Verizon have continued to
  support theirs. Do not design a US product around NB-IoT without written carrier
  confirmation.
- **LTE-M leads on roaming**, which matters for anything that moves across borders.
- **5G RedCap** module pricing and SA network coverage are still the gating factors;
  broader availability is expected through 2027–28.
- **eSIM/eUICC, and specifically SGP.32** (the IoT-focused remote SIM provisioning spec
  finalized in 2024), is now the default expectation for any fleet with a >5-year life or
  multi-country deployment. Design it in; retrofitting carrier flexibility is impossible.

**[UNIVERSAL] Battery-life reality**: the radio dominates. A BLE sensor advertising every
1 s versus every 10 s is roughly a 10× difference in battery life, and no amount of MCU
sleep optimization compensates for a badly chosen connection interval.

### 8.2 BLE — the concepts you actually need

- **GAP** = discovery and connection roles (Peripheral/Central, Broadcaster/Observer).
- **GATT** = the data model: Services contain Characteristics contain Values +
  Descriptors, all addressed by 16-bit (SIG-assigned) or 128-bit (custom) UUIDs.
- **Advertising interval** (20 ms–10.24 s) drives discovery latency and advertiser power.
- **Connection interval** (7.5 ms–4 s, in 1.25 ms units) drives throughput and connected
  power. **Slave latency** lets a peripheral skip N connection events when it has nothing
  to say — this is the single most important BLE power parameter.
- **PHYs**: 1M (default), 2M (double rate, shorter range), Coded S=2/S=8 (long range, 4×
  the airtime).
- **MTU negotiation**: default ATT MTU is 23 bytes (20 bytes of payload). Negotiate up
  (247 is common) or your throughput will be terrible for reasons that look like a bug.
- **Notifications** (no ack, fast) vs **Indications** (acked, one outstanding, slow). Use
  notifications for streaming.

**Bluetooth Core versions [current as of 2026]**: 6.0 (Sept 2024) introduced **Channel
Sounding** — phase-based ranging + round-trip time giving decimetre-level secure ranging,
using 72×1 MHz channels, with ambiguity-free operation to ~150 m. 6.1 (May 2025) added
randomized RPA for privacy. 6.2 (Nov 2025) cut the minimum connection interval from
**7.5 ms to 375 µs** (a big deal for HID and latency-sensitive sensors) and added
amplitude-attack resilience for Channel Sounding. **6.3 was released 6 May 2026**;
the SIG is on a twice-yearly cadence.

### 8.3 Thread and Matter

**Thread**: IPv6 mesh over 802.15.4, with Routers, End Devices, and Sleepy End Devices; a
**Border Router** bridges to the local IP network. Self-healing, no single point of
failure, ~250 kbps.

**Matter**: an *application layer* over IP (Thread, Wi-Fi, or Ethernet) with a Data Model
of Endpoints → Clusters → Attributes/Commands, commissioning via BLE, and a **Fabric**
security model with per-fabric operational certificates (a device can be on several
ecosystems' fabrics simultaneously).

**Current spec state**: **Matter 1.5** (Nov 2025) was the big functional expansion —
**cameras** (WebRTC live A/V, PTZ, detection/privacy zones, STUN/TURN remote access),
**closures**, **soil sensors**, and expanded energy management; **1.5.1** (Mar 2026)
refined cameras/doorbells; **1.6 is reported as the current release as of mid-2026**.
1.4.1/1.4.2 were quality/tooling releases.

**[CONTESTED] Matter's real-world state.** The specification consistently runs ahead of
shipping product and ecosystem app support — a device type can be in the spec for a year
before Apple Home / Google Home / SmartThings expose it usefully. Plan for the
ecosystem-support matrix, not the spec version, and expect commissioning UX to be the
hardest part of your product.

### 8.4 LoRaWAN

- **Classes**: A (uplink-initiated, two short RX windows — lowest power, the default),
  B (scheduled ping slots via beacons — bounded downlink latency), C (continuous RX —
  mains-powered only).
- **Spreading factor** SF7–SF12: higher SF = longer range, exponentially longer airtime,
  lower rate. SF12 packets can be >1 s on air.
- **Duty cycle limits are legal, not advisory** — in EU868, typically 1% per sub-band.
  This *hard-caps* how often you can transmit and how much downlink the network can send.
  Design your telemetry budget around it or your device will be silently throttled.
- **ADR (Adaptive Data Rate)**: the network server tunes SF/power for static devices. Do
  not enable ADR on mobile devices.
- **Join**: **OTAA** (over-the-air activation, derives session keys, supports rejoin —
  always use this) vs **ABP** (hard-coded session keys — a security and frame-counter
  liability; avoid).
- Stack: device → gateway (packet forwarder) → **network server** (ChirpStack, TTN/TTS)
  → application server. Running your own ChirpStack is very achievable and gives you
  data sovereignty.

### 8.5 Application protocols

| Protocol | Transport | Payload | Best for | Watch out for |
|---|---|---|---|---|
| **MQTT 3.1.1 / 5.0** | TCP + TLS | any | Cloud telemetry, UNS, fleet | Broker is a single point of failure; topic design is forever |
| **MQTT-SN** | UDP | any | Sensor networks without TCP | Needs a gateway |
| **CoAP** | UDP + DTLS | CBOR | Very constrained, REST-like | NAT traversal; use Observe for pub/sub-ish |
| **LwM2M** | CoAP | TLV/CBOR/SenML | **Standardized device management** | Fewer cloud integrations than MQTT |
| **HTTP/REST** | TCP + TLS | JSON | Simple, firewall-friendly | Header overhead brutal on cellular/LPWAN |
| **AMQP** | TCP + TLS | any | Enterprise messaging, Azure IoT Hub | Heavy for MCUs |
| **DDS / ROS 2** | UDP multicast | CDR | Robotics, rich QoS policies | Complex; micro-ROS for MCUs |
| **Sparkplug B** | MQTT | Protobuf | Industrial UNS | QoS 0 for DDATA; no retained messages by design |

**MQTT 5 features worth adopting** (and now reachable on MCUs — FreeRTOS's coreMQTT
gained v5 support in the 202604 LTS): **topic aliases** (send the long topic once, then a
2-byte alias — a real win on cellular), **request/response** with correlation data,
**session expiry** and **message expiry intervals**, **shared subscriptions** (load-balance
consumers across a group), and **reason codes** on every ack (so failures are diagnosable
instead of just "disconnected").

**MQTT design rules that prevent regret:**
1. **Design the topic hierarchy once, with one owner.** `{env}/{site}/{area}/{line}/{device}/{signal}`.
   Never put changing values in topics.
2. Use **Last Will and Testament** on every device so "offline" is a first-class state.
3. Publish **retained** messages for state (the current setpoint), non-retained for events.
4. **QoS 1 is almost always right.** QoS 2 costs four round-trips and is rarely justified;
   design your consumers to be idempotent and use QoS 1.
5. Set a **keepalive** appropriate to your network (cellular NAT timeouts often force
   ≤ 240 s) and implement reconnect with **exponential backoff plus jitter** — otherwise
   a broker restart triggers a synchronized thundering herd from your whole fleet.

**Payload encoding on constrained links:**

| Format | Size (typical sensor msg) | Self-describing | Schema needed | Notes |
|---|---|---|---|---|
| JSON | 120 B | yes | no | Debuggable; wasteful |
| **CBOR** (RFC 8949) | ~45 B | yes | no | JSON's data model, binary. Default for CoAP/SUIT |
| MessagePack | ~45 B | yes | no | Similar to CBOR, less standardized |
| **Protobuf** | ~25 B | no | yes | Sparkplug's choice; nanopb for MCUs |
| FlatBuffers | ~30 B | no | yes | Zero-copy read; good for large structures |
| Custom packed struct | ~12 B | no | implicit | Smallest; brittle — version it explicitly |

**[UNIVERSAL] If you roll your own binary format, put a version byte first, and never
reuse a field's meaning.** Field-deployed devices will be on old firmware for years and
your parser must handle every version you ever shipped.

### 8.6 Edge computing and TinyML

**Gateway responsibilities** in a real deployment: protocol translation (Modbus/OPC UA →
MQTT), **store-and-forward** during upstream outage (this is non-negotiable — buffer to
flash with a bounded ring), local rule evaluation for latency-critical reactions,
aggregation/downsampling to control cloud cost, and being the security boundary.

**On-device ML in 2026:**
- **LiteRT for Microcontrollers** (formerly TensorFlow Lite Micro) remains the most
  widely used MCU runtime — the core runtime fits in ~16 KB on a Cortex-M3.
- **ExecuTorch** is the PyTorch-native path, growing fast, strongest where an NPU exists.
- **Arm Ethos-U** micro-NPUs (U55, U65, **U85**) sit beside Cortex-M cores; the **Vela**
  compiler converts LiteRT models to NPU form. U85 adds **transformer operator support**
  and native TOSA, which is what makes small language models on MCU-class hardware
  plausible rather than a stunt.
- **Vendor SDKs**: STM32Cube.AI, NXP eIQ, Renesas e-AI — best per-family performance and
  IDE integration, at the cost of portability.
- **Edge Impulse** and similar: excellent end-to-end tooling for data collection →
  training → deployment; the right choice for prototyping and for teams without ML
  engineers; constraining when you need custom architectures.
- The ecosystem has converged on **ONNX as the interchange format and INT8 quantization
  as the default precision.**
- **The metric that matters is energy per inference**, not inference latency, for anything
  battery-powered. Benchmark with **MLPerf Tiny**, which includes energy measurement.

**Practical TinyML advice**: quantization-aware training beats post-training quantization
when accuracy is marginal; the model is rarely the bottleneck — **feature extraction (FFT,
MFCC, windowing) often dominates both compute and RAM**; and always compute peak RAM as
`max over layers of (input tensor + output tensor + workspace)`, because that number, not
model size, is what fails to fit.

---

## §9. Cloud, Fleet, and Lifecycle

### 9.1 Platform landscape (2026)

- **AWS IoT Core** — MQTT broker + device registry, **Device Shadow** (desired/reported
  state), **Jobs** (fleet operations), **Fleet Provisioning**, **Device Defender**
  (behaviour anomaly detection), **SiteWise** (industrial asset models), **Greengrass v2**
  (edge runtime with components). **⚠️ Greengrass V1 support ends 7 October 2026** —
  migrate to V2.
- **Azure IoT** — **IoT Hub** for device-to-cloud at scale (MQTT/AMQP/HTTPS), **DPS** for
  zero-touch provisioning, **Azure Digital Twins**, and **Azure IoT Operations** as the
  newer Arc-enabled, Kubernetes-native edge platform for industrial/OT: an edge-native
  MQTT broker, OPC UA / ONVIF / media / REST / MQTT connectors, dataflows into Event
  Hubs / Event Grid / Microsoft Fabric, and up to **72 hours of offline operation**.
  Recent releases (2510, 2603) added MQTT data persistence, X.509 auth via Device
  Registry, no-code dataflow graphs, cloud-to-edge management actions, and unified health
  reporting. **Note on IoT Central**: a February 2024 console message announcing
  retirement on 31 March 2027 was **retracted by Microsoft as erroneous**; the current
  Azure IoT portfolio is documented as IoT Hub + IoT Operations. Verify status directly
  before making a platform bet.
- **Google Cloud IoT Core is gone** (retired 16 August 2023). There is no managed device
  connectivity service on GCP; users moved to partners (ClearBlade, Litmus) or to AWS/Azure.
  This is the industry's standing reminder that **your device-side protocol should be
  standard MQTT/TLS so the broker is replaceable.**
- **Self-hosted / independent**: **EMQX**, **HiveMQ**, **Mosquitto** (brokers);
  **ThingsBoard** (full platform); **ChirpStack** (LoRaWAN); **Balena** (fleet + container
  OS); **Golioth**, **Memfault** (device management/observability, MCU-focused);
  **Particle** (vertically integrated); **Home Assistant / ESPHome** (prosumer).

**[UNIVERSAL, learned the hard way] Architect so the cloud is replaceable.** Standard MQTT
over TLS with X.509, a documented topic schema, and a payload format you own. Every
proprietary device-side SDK you adopt is a migration cost you're pre-paying.

### 9.2 Identity and provisioning

**The chain of trust:**
```
Silicon root of trust (immutable ROM / fuses)
  └─ verifies bootloader signature (MCUboot, ESP secure boot, TF-M)
       └─ verifies application signature
            └─ application uses a device identity key that NEVER leaves the secure element
                 └─ TLS mutual auth to the cloud presents a device certificate
```

**Where the private key lives** determines your whole security posture:
- **Secure element** (ATECC608, NXP SE050, Infineon OPTIGA): key generated on-chip, never
  extractable, hardware ECDSA. ~$0.50–1.50 BOM. **The right answer for most products.**
- **TrustZone-M + Trusted Firmware-M (TF-M)**: key in the secure partition, PSA Crypto API
  from the non-secure app. No extra BOM; requires an M33/M23-class part and real
  engineering effort.
- **Flash with readout protection**: cheapest, weakest. RDP levels are bypassable with
  fault injection on many parts. Acceptable only when the threat model genuinely tolerates
  a cloned device.
- **PSA Certified** (Level 1/2/3) and **SESIP** are the certification schemes that let you
  make a defensible claim about which of the above you did.

**Provisioning patterns:**
- **Factory-injected certificate**: device gets a unique cert at manufacture from your PKI.
  Most control; requires a secure manufacturing process and an HSM-backed CA.
- **Just-in-time registration / provisioning (JITR/JITP)**: device presents a cert signed
  by your CA; the cloud auto-registers it on first connect. Scales well.
- **Claim-based / fleet provisioning**: device ships with a *shared* bootstrap credential,
  exchanges it for a unique one on first connect. Convenient; the shared credential is the
  weak link — rotate it and bound its privileges hard.
- **DICE** (Device Identifier Composition Engine): derives a layered identity from an
  immutable UDS and the measurement of each boot stage, so identity is cryptographically
  bound to the firmware actually running.

> **⚠️ GOTCHA — RNG entropy.** Key generation and TLS both need a real TRNG. Many MCUs'
> "RNG" is a PRNG seeded from something weak, and some vendor implementations have shipped
> with broken entropy. If keys are generated on-device, use the hardware TRNG, verify it
> exists (not all part variants have it), and run at least a smoke test (NIST SP 800-90B
> health tests) at boot. Duplicate keys across a fleet is a catastrophic, unrecoverable,
> and historically common failure.

### 9.3 OTA update

**[UNIVERSAL] Non-negotiable properties of a firmware update system:**
1. **Authenticated** — signature verified before execution, key in immutable storage.
2. **Atomic** — the device is never left in a half-updated, unbootable state.
3. **Rollback-capable** — automatic revert if the new image fails to confirm health.
4. **Anti-rollback** — a monotonic security counter prevents an attacker re-flashing an
   old, vulnerable-but-validly-signed image.
5. **Power-fail-safe** — losing power at any instant leaves a bootable device.
6. **Staged** — canary → percentage rollout → full fleet, with automatic halt on error-rate
   regression.

**Mechanisms:**
- **A/B (dual bank)**: two full slots; write inactive, swap the boot pointer, confirm.
  Needs 2× flash. Simplest to reason about. **MCUboot** implements swap, overwrite-only,
  and **DirectXIP** (execute from either slot, no copy) modes.
- **Delta / differential**: ship only the binary diff. 10–50× smaller, essential on LPWAN
  and cellular-metered links. Costs the device RAM/CPU for patching and requires exact
  knowledge of the currently-installed version.
- **Bootloader OTA**: updating the bootloader itself is the riskiest operation you can
  perform. Some silicon now provides ROM-level recovery — **ESP-IDF v6.0 added recovery
  bootloader support on ESP32-C5/C61**, where the ROM falls back to a recovery partition
  if the primary bootloader fails to load. Without such a fallback, bootloader OTA has no
  safety net; treat it accordingly.

**Standards**: **RFC 9019** (SUIT firmware update architecture for IoT) and **RFC 9124**
(information model) define a CBOR-based manifest approach; **Uptane** is the
automotive-grade framework (derived from TUF) designed to survive a compromised update
server.

**Post-quantum firmware signing — start planning now.** Firmware signed today may need to
be verified by a device in 2040. **NIST SP 800-208** standardizes the stateful hash-based
signature schemes **LMS** (RFC 8554) and **XMSS** (RFC 8391); NSA's **CNSA 2.0** names
**software/firmware signing as the highest-priority post-quantum transition**, advising
adoption preferentially by 2025 and exclusively by 2030. Note the operational catch:
stateful HBS schemes **must never reuse a one-time key**, so SP 800-208 requires key
generation and signing inside a FIPS 140 Level 3 HSM that cannot export the private key —
meaning "restore the signing key from backup" is a security incident, not a recovery
procedure. **SLH-DSA (FIPS 205)** is the stateless alternative; **ML-DSA (FIPS 204)** is
the general-purpose lattice signature. RFC 9019 itself recommends post-quantum signatures
for immutable ROM bootloader code.

### 9.4 Fleet observability

**[UNIVERSAL] You cannot debug what you cannot see, and you cannot reproduce field
conditions on your desk.** The four things every shipped device should report:
1. **Reset reason** on every boot (§1.3 → `embedded-silicon-and-firmware-models`) — the earliest regression signal you have.
2. **Crash captures**: the fault registers and stacked frame from §5.8 → `embedded-languages-realtime-and-patterns`, plus ideally a
   coredump, symbolicated server-side against the exact build's ELF.
3. **Heartbeat metrics**: uptime, free heap / stack high-water marks, RSSI, battery,
   error counters, task deadline misses.
4. **Structured events**, not free-text logs — a numeric event ID plus binary arguments,
   decoded server-side (the `defmt` / Memfault / trace-recorder approach). This is 10–50×
   cheaper in flash, bandwidth, and CPU than `printf` strings.

**Metrics to alert on**: crash-free-hours per device, watchdog reset rate, OTA success
rate by cohort, connection churn, and battery depletion slope. A firmware regression shows
up in crash-free-hours long before it shows up in support tickets.

**Digital twin / shadow pattern**: cloud holds `desired` and `reported` state; the device
reconciles toward `desired` and publishes `reported`. This makes configuration
eventually-consistent and survivable across offline periods, which naive command-push does
not. Implement it even if you're not on a platform that gives it to you.
